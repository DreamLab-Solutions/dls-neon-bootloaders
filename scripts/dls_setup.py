#!/usr/bin/env python3
"""DreamLab theme chooser. Preview is unprivileged; boot writes are explicit."""
import argparse
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

THEMES = ('event-horizon', 'quantum-fabric', 'sentient-atlas', 'synaptic-cosmos')
PROFILES = ('720p', '1080p', '1440p', '4k')
BASE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular(path):
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise RuntimeError('File assente o collegamento non consentito: ' + str(path))
    return path.read_bytes()


def member(base, name):
    p = Path(name)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise RuntimeError('Percorso non valido nel pacchetto')
    result = base / p
    regular(result)
    return result


def verify_bundle(base):
    manifest = json.loads(regular(base / 'manifest.json'))
    for name, expected in manifest.items():
        if sha(regular(member(base, name))) != expected:
            raise RuntimeError('Pacchetto modificato: ' + name)
    required = {'dls-neon-setup', 'grub_manager.py', 'limine_manager.py', 'catalog.json'}
    if not required <= set(manifest):
        raise RuntimeError('Manifest del pacchetto incompleto')
    catalog = json.loads(regular(base / 'catalog.json'))
    if set(catalog) != set(THEMES):
        raise RuntimeError('Catalogo inatteso')
    for slug, item in catalog.items():
        for backend in ('grub', 'limine'):
            expected = f'{backend}/themes/{slug}/manifest.json'
            preview = f'previews/{backend}/{slug}.png'
            if item[backend] != f'{backend}/themes/{slug}' or item['preview'][backend] != preview:
                raise RuntimeError('Percorso del catalogo inatteso')
            if expected not in manifest or preview not in manifest:
                raise RuntimeError('Tema o anteprima non verificabile')
    return catalog


def load_manager(base, backend):
    path = member(base, backend + '_manager.py')
    spec = importlib.util.spec_from_file_location('dls_' + backend, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def detected_backend(root=Path('/')):
    if not (root/'sys/firmware/efi').is_dir():
        raise RuntimeError('Avvio UEFI non verificabile: anteprime disponibili, applicazione da Linux UEFI con GRUB o Limine')
    boot=subprocess.check_output(['efibootmgr','-v'],text=True)
    current=re.search(r'^BootCurrent: ([0-9a-fA-F]{4})$',boot,re.M)
    line=next((x for x in boot.splitlines() if current and x.startswith('Boot'+current[1])), '')
    file=re.search(r'File\(([^)]+)\)',line,re.I)
    path=file[1].replace('\\','/').lower() if file else ''
    if path.endswith('/limine_x64.efi'):return 'limine'
    if path.endswith(('/grubx64.efi','/shimx64.efi')):return 'grub'
    raise RuntimeError('La voce UEFI attiva non è GRUB/Limine. Windows Boot Manager e il loader Apple non usano questi temi; nessun bootloader sarà sostituito.')


def grub_guard():
    if os.uname().machine!='x86_64' or detected_backend()!='grub':
        raise RuntimeError('Occorre GRUB attivo in UEFI x86-64')
    boot=subprocess.check_output(['efibootmgr','-v'],text=True)
    current=re.search(r'^BootCurrent: ([0-9a-fA-F]{4})$',boot,re.M)
    line=next((x for x in boot.splitlines() if current and x.startswith('Boot'+current[1])), '')
    match=re.search(r'HD\(\d+,GPT,([0-9a-f-]+),[^)]*\).*File\((\\EFI\\[^)]+\\(?:shimx64|grubx64)\.efi)\)',line,re.I)
    if not match:raise RuntimeError('Percorso EFI GRUB e partizione GPT non verificabili')
    mounts=json.loads(subprocess.check_output(['findmnt','-J','-t','vfat','-o','TARGET,SOURCE,FSTYPE'],text=True))['filesystems']
    matched=[]
    for mount in mounts:
        partuuid=subprocess.check_output(['lsblk','-dnro','PARTUUID',mount['source']],text=True).strip()
        if partuuid.lower()==match[1].lower():matched.append(Path(mount['target']))
    if len(matched)!=1:raise RuntimeError('La ESP montata non corrisponde univocamente alla voce UEFI attiva')
    binary=matched[0]/match[2].replace('\\','/').lstrip('/')
    regular(binary);regular(binary.with_name('grubx64.efi'))
    configs=[p for p in ('boot/grub/grub.cfg','boot/grub2/grub.cfg') if Path('/'+p).is_file()]
    if len(configs)!=1:raise RuntimeError('Configurazione GRUB assente o ambigua: verificare /boot/grub e /boot/grub2')
    tools={}
    for key,name in [('check','script-check'),('probe','probe'),('relpath','mkrelpath')]:
        tool=shutil.which('grub-'+name) or shutil.which('grub2-'+name)
        if not tool:raise RuntimeError('Manca il programma GRUB '+name)
        tools[key]=tool
    return {'config':configs[0],'tools':tools}


def menu_titles(module, text):
    titles=[shlex.split(header)[0] for header in module.boot_entries(text)]
    if module.has_bls_menu(text):
        titles.append('BLS: voci dinamiche della distribuzione, file originali conservati')
    return titles


def plan(base, backend, theme, profile, timeout):
    catalog = verify_bundle(base)
    if backend != detected_backend():
        raise RuntimeError('Bootloader richiesto diverso dal target del sistema; nessuna migrazione automatica')
    module = load_manager(base, backend)
    platform = {}
    if backend == 'limine':
        module.host_guard()
    else:
        platform = grub_guard()
    source = base / catalog[theme][backend]
    config_rel = 'boot/limine.conf' if backend=='limine' else platform['config']
    config = Path('/'+config_rel)
    state = Path('/var/lib/dls-neon-' + backend)
    active, pending = state / 'active.json', state / 'pending.json'
    if pending.exists():
        raise RuntimeError('Transazione interrotta: usare status/recovery prima del selettore')
    before = regular(config)
    manager = module.Manager() if backend=='limine' else module.Manager(config=config_rel,tools=platform['tools'])
    can_apply, reason = True, ''
    if backend == 'limine':
        key, _, _ = module.assets(source)
        current = json.loads(regular(active)) if active.exists() else None
        if current:
            if sha(before) != current['after']:
                raise RuntimeError('Configurazione aggiornata dopo il tema: serve revisione manuale')
            manager.owned_assets(current)
        if current and current['asset'] == key:
            can_apply, reason = False, 'Questo tema è già attivo.'
        elif (Path('/boot/dls-neon-limine') / key).exists():
            can_apply, reason = False, 'Tema conservato nella cronologia: usare Ripristina precedente.'
        else:
            manager.plan(source, replace=bool(current))
    else:
        module.verify_assets(source)
        if not module.has_native_menu(before.decode()):
            raise RuntimeError('Configurazione GRUB senza voci riconoscibili')
        if active.exists() and json.loads(regular(active)).get('status') != 'active':
            raise RuntimeError('Transazione GRUB incompleta: seguire la procedura di recovery')
        if active.exists():
            can_apply, reason = False, 'Ripristinare il tema GRUB attivo prima di sceglierne un altro.'
    record = {'backend': backend, 'theme': theme, 'title': catalog[theme]['title'],
              'profile': profile if backend == 'grub' else 'native',
              'timeout': timeout if backend == 'grub' else 'invariato',
              'config_sha256': sha(before), 'bundle_sha256': sha(regular(base / 'manifest.json')),
              'active_sha256': sha(regular(active)) if active.exists() else None,
              'can_apply': can_apply, 'can_restore': active.exists(), 'reason': reason,
              'config_path':config_rel,'grub_tools':platform.get('tools'),
              'entries':([line.lstrip('/+').strip() for line in before.decode().splitlines() if line.startswith('/')] if backend=='limine' else menu_titles(module,before.decode())),
              'boot_entries': 'conservate senza rigenerare o filtrare sistemi operativi',
              'reboot': False}
    record['review_sha256'] = sha(json.dumps(record, sort_keys=True).encode())
    return record


def operation(base, args):
    if os.geteuid() != 0:
        raise RuntimeError('La verifica del sistema richiede autenticazione amministratore')
    if args.action != 'plan' and (not args.approve_boot_write or not args.recovery_confirmed):
        raise RuntimeError('Servono approvazione esplicita e conferma di backup/recovery')
    record = plan(base, args.backend, args.theme, args.profile, args.timeout)
    if args.action == 'plan':
        return record
    if record['review_sha256'] != args.expected_review:
        raise RuntimeError('Il piano o il sistema è cambiato: ripetere Verifica piano')
    module = load_manager(base, args.backend)
    manager = module.Manager() if args.backend=='limine' else module.Manager(config=record['config_path'],tools=record['grub_tools'])
    if args.action == 'apply':
        if not record['can_apply']:
            raise RuntimeError(record['reason'])
        source = base / json.loads(regular(base / 'catalog.json'))[args.theme][args.backend]
        with redirect_stdout(io.StringIO()):
            if args.backend == 'limine':
                manager.install(source, expected=record['config_sha256'], replace=record['can_restore'])
            else:
                # Recheck the reviewed GRUB baseline immediately before its transaction.
                if sha(regular(Path('/'+record['config_path']))) != record['config_sha256']:
                    raise RuntimeError('Configurazione modificata dopo la revisione')
                manager.install(source, args.profile, args.timeout, expected_config=record['config_sha256'])
        result = 'Tema applicato e verificato nei file. Il prossimo riavvio resta da verificare.'
    else:
        if not record['can_restore']:
            raise RuntimeError('Nessun checkpoint da ripristinare')
        with redirect_stdout(io.StringIO()):
            manager.restore()
        result = 'Aspetto precedente ripristinato nei file; backup conservato.'
    os.sync()
    return {'result': result, 'hardware_boot_verified': False}


class Console:
    """Terminal interaction; browsing never requires administrative access."""
    def __init__(self, base, read=input, write=print, execute=None, preview=None):
        self.base,self.read,self.write=base,read,write
        self.catalog=verify_bundle(base)
        self.theme,self.backend,self.preview_backend='synaptic-cosmos',None,'limine'
        self.profile,self.timeout='1080p',8
        self.review=None
        self.execute=execute or self.system
        self.preview=preview or self.open_preview

    def system(self, action, extra=()):
        command=([sys.executable] if os.geteuid()==0 else ['sudo','/usr/bin/python3'])+[str(self.base/'dls-neon-setup'),action]
        if action!='detect':
            command+=['--backend',self.backend,'--theme',self.theme,'--profile',self.profile,'--timeout',str(self.timeout)]
        command+=list(extra)
        result=subprocess.run(command,text=True,capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or 'Autenticazione o operazione annullata')
        return json.loads(result.stdout)

    def open_preview(self, path):
        # Use the desktop viewer, never a shell or an administrator GUI.
        if os.geteuid()!=0 and shutil.which('xdg-open'):
            subprocess.Popen(['xdg-open',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.write('Anteprima: '+str(path))

    def detect(self):
        result=self.execute('detect')
        self.backend=result['backend'];self.preview_backend=self.backend;self.review=None
        self.write('Bootloader attivo rilevato: '+self.backend.upper())

    def show_plan(self):
        if self.backend is None:self.detect()
        self.review=self.execute('plan')
        result=self.review
        self.write('\nPiano: '+result['title']+' · '+result['backend'].upper())
        self.write('Configurazione: /'+result['config_path'])
        self.write('Voci conservate, senza rilevarle di nuovo:')
        for title in result['entries']:
            self.write('  • '+re.sub(r'[\x00-\x1f\x7f-\x9f]','?',title))
        if self.backend=='grub':self.write(f'Profilo {self.profile}; menu visibile; attesa {self.timeout} secondi.')
        else:self.write('Risoluzione, default e attesa Limine invariati.')
        self.write(result['reason'] or 'Piano verificato. Nessun file di avvio è stato modificato.')

    def apply(self, action):
        if not self.review:
            self.write('Prima verifica il piano con v.');return
        allowed='can_apply' if action=='apply' else 'can_restore'
        if not self.review[allowed]:
            self.write(self.review['reason'] or 'Operazione non disponibile.');return
        if self.read('Backup indipendente e chiavetta live UEFI verificati? [s/N] ').strip().lower()!='s':
            self.write('Operazione annullata.');return
        word='APPLICA' if action=='apply' else 'RIPRISTINA'
        if self.read(f'Scrivi {word} per confermare la modifica dei file di avvio: ').strip()!=word:
            self.write('Operazione annullata.');return
        result=self.execute(action,['--approve-boot-write','--recovery-confirmed','--expected-review',self.review['review_sha256']])
        self.review=None;self.write(result['result'])

    def run(self):
        self.write('DreamLab · Temi di avvio · console interattiva')
        self.write('Windows, macOS, Linux e voci personalizzate già presenti restano della distribuzione.')
        self.write('Sfogliare e aprire le anteprime non richiede sudo. q esce senza modifiche.')
        while True:
            self.write('\n'+ '  |  '.join(f'{n} {self.catalog[slug]["title"]}'+(' *' if slug==self.theme else '') for n,slug in enumerate(THEMES,1)))
            self.write(f'Anteprima: {self.preview_backend.upper()} · p apri immagine · b cambia anteprima GRUB/Limine')
            self.write('d rileva bootloader · v verifica piano · o profilo/attesa GRUB · a applica · r ripristina · q esci')
            try:
                choice=self.read('Scelta: ').strip().lower()
                if choice in {'q','0','esci'}:return
                if choice in {'1','2','3','4'}:
                    self.theme=THEMES[int(choice)-1];self.review=None
                elif choice=='p':
                    name=self.catalog[self.theme]['preview'][self.preview_backend]
                    self.preview(member(self.base,name))
                elif choice=='b':self.preview_backend='grub' if self.preview_backend=='limine' else 'limine'
                elif choice=='d':self.detect()
                elif choice=='v':self.show_plan()
                elif choice=='o':
                    profile=self.read('Profilo GRUB [720p/1080p/1440p/4k]: ').strip()
                    timeout=self.read('Attesa GRUB [1–60 secondi]: ').strip()
                    if profile not in PROFILES or not timeout.isdigit() or not 1<=int(timeout)<=60:
                        self.write('Valori non validi: impostazioni precedenti conservate.');continue
                    self.profile,self.timeout=profile,int(timeout);self.review=None
                elif choice in {'a','r'}:self.apply('apply' if choice=='a' else 'restore')
                else:self.write('Scelta non riconosciuta.')
            except (EOFError,KeyboardInterrupt):self.write('\nUscita senza ulteriori operazioni.');return
            except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
                self.review=None;self.write('Operazione non eseguita: '+str(error))
                self.write('Puoi continuare a scegliere/aprire anteprime oppure uscire.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',nargs='?',choices=('console','detect','plan','apply','restore'),default='console')
    parser.add_argument('--backend',choices=('grub','limine'))
    parser.add_argument('--theme',choices=THEMES,default='synaptic-cosmos')
    parser.add_argument('--profile',choices=PROFILES,default='1080p')
    parser.add_argument('--timeout',type=int,choices=range(1,61),default=8)
    parser.add_argument('--expected-review')
    parser.add_argument('--approve-boot-write',action='store_true')
    parser.add_argument('--recovery-confirmed',action='store_true')
    args=parser.parse_args()
    try:
        if args.action=='console':Console(BASE).run()
        elif args.action=='detect':
            if os.geteuid()!=0:raise RuntimeError('La lettura UEFI richiede sudo')
            print(json.dumps({'backend':detected_backend()}))
        else:
            if not args.backend:parser.error('--backend richiesto')
            print(json.dumps(operation(BASE,args),ensure_ascii=False))
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr);sys.exit(1)


if __name__=='__main__':main()
