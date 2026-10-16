#!/usr/bin/env python3
"""DreamLab theme chooser. Preview is unprivileged; boot writes are explicit."""
import argparse
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import queue
import re
import shlex
import subprocess
import sys
import threading

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


def distro(root=Path('/')):
    path = root / 'etc/os-release'
    if path.is_symlink():
        resolved = path.resolve(strict=True)
        if resolved != (root / 'usr/lib/os-release').resolve(strict=True):
            raise RuntimeError('Destinazione os-release non standard')
        path = resolved
    values = {}
    for line in regular(path).decode().splitlines():
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            tokens = shlex.split(value)
            values[key] = tokens[0] if len(tokens) == 1 else ''
    return values.get('ID', '')


def detected_backend(root=Path('/')):
    identity = distro(root)
    if identity == 'omarchy':
        return 'limine'
    if identity in {'ubuntu', 'debian'}:
        return 'grub'
    raise RuntimeError('Sistema non qualificato: supportati Ubuntu/Debian con GRUB e Omarchy con Limine 12.8')


def load_manager(base, backend):
    path = member(base, backend + '_manager.py')
    spec = importlib.util.spec_from_file_location('dls_' + backend, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grub_guard():
    if os.uname().machine != 'x86_64' or not Path('/sys/firmware/efi').is_dir():
        raise RuntimeError('Il selettore qualifica GRUB soltanto su UEFI x86-64')
    boot = subprocess.check_output(['efibootmgr', '-v'], text=True)
    current = re.search(r'^BootCurrent: ([0-9a-fA-F]{4})$', boot, re.M)
    line = next((x for x in boot.splitlines() if current and x.startswith('Boot' + current[1])), '')
    match = re.search(r'HD\(\d+,GPT,([0-9a-f-]+),[^)]*\).*File\((\\EFI\\(?:ubuntu|debian)\\(?:shimx64|grubx64)\.efi)\)', line, re.I)
    if not match:
        raise RuntimeError('La voce UEFI attiva non identifica il GRUB Ubuntu/Debian qualificato')
    mounted = json.loads(subprocess.check_output(['findmnt', '-J', '-M', '/boot/efi', '-o', 'TARGET,SOURCE,FSTYPE'], text=True))['filesystems'][0]
    if mounted['fstype'] != 'vfat':
        raise RuntimeError('ESP FAT non montata in /boot/efi')
    partuuid = subprocess.check_output(['lsblk', '-dnro', 'PARTUUID', mounted['source']], text=True).strip()
    if partuuid.lower() != match[1].lower():
        raise RuntimeError('La ESP montata non corrisponde alla voce UEFI attiva')
    folder = Path('/boot/efi') / match[2].replace('\\', '/').lstrip('/')
    # A shim entry qualifies only when its sibling GRUB executable also exists.
    regular(folder)
    regular(folder.with_name('grubx64.efi'))
    regular(Path('/etc/default/grub'))
    subprocess.run(['grub-mkconfig', '--version'], check=True, capture_output=True)


def plan(base, backend, theme, profile, timeout):
    catalog = verify_bundle(base)
    if backend != detected_backend():
        raise RuntimeError('Bootloader richiesto diverso dal target del sistema; nessuna migrazione automatica')
    module = load_manager(base, backend)
    if backend == 'limine':
        module.host_guard()
    else:
        grub_guard()
    source = base / catalog[theme][backend]
    config = Path('/boot/limine.conf' if backend == 'limine' else '/boot/grub/grub.cfg')
    state = Path('/var/lib/dls-neon-' + backend)
    active, pending = state / 'active.json', state / 'pending.json'
    if pending.exists():
        raise RuntimeError('Transazione interrotta: usare status/recovery prima del selettore')
    before = regular(config)
    manager = module.Manager()
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
        if not module.boot_entries(before.decode()):
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
              'boot_entries': 'conservate; verifica prima della sostituzione',
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
    manager = module.Manager()
    if args.action == 'apply':
        if not record['can_apply']:
            raise RuntimeError(record['reason'])
        source = base / json.loads(regular(base / 'catalog.json'))[args.theme][args.backend]
        with redirect_stdout(io.StringIO()):
            if args.backend == 'limine':
                manager.install(source, expected=record['config_sha256'], replace=record['can_restore'])
            else:
                # Recheck the reviewed GRUB baseline immediately before its transaction.
                if sha(regular(Path('/boot/grub/grub.cfg'))) != record['config_sha256']:
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


class Wizard:
    def __init__(self, window, base, executor=None):
        import tkinter as tk
        from tkinter import ttk, messagebox
        self.tk, self.ttk, self.messagebox = tk, ttk, messagebox
        style = ttk.Style(window); style.theme_use('clam')
        style.configure('.', background='#071723', foreground='#E7F2EE')
        style.configure('TButton', background='#00A49A', foreground='#071723', padding=8)
        style.map('TButton', background=[('disabled','#273743'),('active','#30D4BA')], foreground=[('disabled','#B5CEC8')])
        style.configure('TCombobox', fieldbackground='#273743', background='#00A49A', foreground='#E7F2EE')
        style.map('TCombobox', fieldbackground=[('readonly','#273743')], selectbackground=[('readonly','#273743')], selectforeground=[('readonly','#E7F2EE')])
        style.configure('Title.TLabel', foreground='#D9FF00')
        window.configure(background='#071723')
        self.window, self.base = window, base
        self.catalog = verify_bundle(base)
        self.executor = executor or self.execute
        self.events = queue.Queue()
        self.busy, self.review = False, None
        self.preview_cache, self.preview_signature = {}, None
        self.theme = tk.StringVar(value='synaptic-cosmos')
        self.profile, self.timeout = tk.StringVar(value='1080p'), tk.IntVar(value=8)
        self.recovery = tk.BooleanVar(value=False)
        try:
            self.backend = detected_backend()
            target = 'Omarchy · Limine 12.8' if self.backend == 'limine' else 'Ubuntu/Debian · GRUB UEFI'
        except (OSError, RuntimeError) as error:
            self.backend, target = None, str(error)
        self.preview_backend = tk.StringVar(value=self.backend or 'limine')
        self.status = tk.StringVar(value='Scegli un tema. La verifica del piano legge il sistema senza modificarlo.')
        window.title('DreamLab · Temi di avvio')
        window.geometry('1180x880')
        window.minsize(900, 760)
        frame = ttk.Frame(window, padding=18); frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='DreamLab · Scegli il tuo universo', font=('', 20, 'bold'), style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame, text='Target: ' + target).pack(anchor='w', pady=(4, 12))
        self.inputs = []
        choices = ttk.Frame(frame); choices.pack(fill='x')
        for slug in THEMES:
            b = ttk.Radiobutton(choices, text=self.catalog[slug]['title'], value=slug, variable=self.theme, command=self.change)
            b.pack(side='left', padx=(0, 18)); self.inputs.append(b)
        tools = ttk.Frame(frame); tools.pack(fill='x', pady=10)
        ttk.Label(tools, text='Anteprima menu:').pack(side='left')
        combo = ttk.Combobox(tools, values=('limine','grub'), textvariable=self.preview_backend, state='readonly', width=10)
        combo.pack(side='left', padx=8); combo.bind('<<ComboboxSelected>>', lambda _: self.show_preview()); self.inputs.append(combo)
        ttk.Label(tools, text='Immagini da bootloader reale in VM · voci dimostrative · il firmware può usare un’altra risoluzione').pack(side='left')
        self.picture = ttk.Label(frame, anchor='center'); self.picture.pack(fill='both', expand=True)
        self.caption = ttk.Label(frame, anchor='center'); self.caption.pack(fill='x', pady=4)
        settings = ttk.Frame(frame); settings.pack(fill='x', pady=6)
        ttk.Label(settings, text='GRUB: profilo').pack(side='left')
        profile = ttk.Combobox(settings, values=PROFILES, textvariable=self.profile, width=8, state='readonly')
        profile.pack(side='left', padx=6); self.inputs.append(profile)
        ttk.Label(settings, text='Attesa GRUB (secondi)').pack(side='left')
        timeout = ttk.Spinbox(settings, from_=1, to=60, textvariable=self.timeout, width=5)
        timeout.pack(side='left', padx=6); self.inputs.append(timeout)
        ttk.Label(settings, text='Limine conserva risoluzione, attesa e impostazioni native.').pack(side='left', padx=10)
        self.profile.trace_add('write', lambda *_: self.invalidate())
        self.timeout.trace_add('write', lambda *_: self.invalidate())
        self.check = ttk.Checkbutton(frame, text='Ho verificato la copia indipendente del backup e una chiavetta live UEFI utilizzabile.', variable=self.recovery, command=self.buttons)
        self.check.pack(anchor='w', pady=6)
        ttk.Label(frame, textvariable=self.status, wraplength=1100).pack(fill='x', pady=6)
        actions = ttk.Frame(frame); actions.pack(fill='x')
        self.check_plan = ttk.Button(actions, text='1 · Verifica piano (sola lettura)', command=lambda: self.start('plan'))
        self.apply = ttk.Button(actions, text='2 · Applica tema', command=lambda: self.confirm('apply'))
        self.restore = ttk.Button(actions, text='Ripristina precedente', command=lambda: self.confirm('restore'))
        for button in (self.check_plan,self.apply,self.restore): button.pack(side='left', padx=(0,10))
        window.protocol('WM_DELETE_WINDOW', self.close)
        self.show_preview(); self.buttons(); self.timer = window.after(100, self.poll)
        window.bind('<Configure>', self.resize)

    def invalidate(self):
        self.review = None
        self.buttons()

    def change(self):
        self.invalidate(); self.show_preview()

    def show_preview(self):
        slug, backend = self.theme.get(), self.preview_backend.get()
        path = member(self.base, self.catalog[slug]['preview'][backend])
        cache_key = (slug, backend)
        if cache_key not in self.preview_cache:
            self.preview_cache[cache_key] = self.tk.PhotoImage(file=str(path))
        original = self.preview_cache[cache_key]
        width = max(700, min(1100, self.window.winfo_width()-60))
        height = max(300, min(560, self.window.winfo_height()-320))
        factor = max(1, math.ceil(original.width()/width), math.ceil(original.height()/height))
        signature = (slug, backend, factor)
        if self.preview_signature == signature:
            return
        self.preview_signature = signature
        self.image = original.subsample(factor)
        self.picture.configure(image=self.image)
        self.caption.configure(text=f'{self.catalog[slug]["title"]} · {backend.upper()} · 1080p · anteprima VM')

    def resize(self, event):
        if event.widget is self.window and event.width > 100:
            self.show_preview()

    def buttons(self):
        active = not self.busy and self.backend is not None
        self.check_plan.configure(state='normal' if active else 'disabled')
        approved = active and self.review is not None and self.recovery.get()
        for button, key in [(self.apply,'can_apply'),(self.restore,'can_restore')]:
            button.configure(state='normal' if approved and self.review.get(key) else 'disabled')

    def execute(self, action):
        command = ['pkexec', '/usr/bin/python3', str(self.base/'dls-neon-setup'), action,
                   '--backend', self.backend, '--theme', self.theme.get(),
                   '--profile', self.profile.get(), '--timeout', str(self.timeout.get())]
        if action != 'plan':
            command += ['--approve-boot-write', '--recovery-confirmed', '--expected-review', self.review['review_sha256']]
        return command

    def start(self, action):
        if self.busy: return
        try:
            command = self.executor(action)
        except (ValueError, self.tk.TclError) as error:
            self.status.set(str(error)); return
        self.busy = True
        for widget in self.inputs: widget.configure(state='disabled')
        self.check.configure(state='disabled'); self.buttons()
        self.status.set('Autenticazione e verifica in corso…' if action == 'plan' else 'Operazione in corso. Attendi il risultato.')
        def work():
            try:
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                self.events.put((action, json.loads(result.stdout), None))
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                self.events.put((action,None,getattr(error,'stderr',None) or str(error)))
        threading.Thread(target=work, daemon=True).start()

    def confirm(self, action):
        if not self.review or not self.recovery.get() or self.busy: return
        text = ('Applicare ' + self.review['title'] if action == 'apply' else 'Ripristinare il tema precedente')
        text += '?\nSaranno modificati i file grafici di avvio. Il backup di transazione viene conservato. Nessun riavvio automatico.'
        if self.messagebox.askyesno('Conferma modifica dell’avvio', text): self.start(action)

    def poll(self):
        try:
            action, result, error = self.events.get_nowait()
        except queue.Empty:
            self.timer = self.window.after(100,self.poll); return
        self.busy = False
        for widget in self.inputs:
            widget.configure(state='readonly' if isinstance(widget,self.ttk.Combobox) else 'normal')
        self.check.configure(state='normal')
        if error:
            self.review = None; self.status.set('Operazione fermata: ' + error.strip())
        elif action == 'plan':
            self.review = result
            text = result['reason'] or ('Piano verificato per ' + result['title'] + '. Backup di transazione e controllo delle voci inclusi.')
            if self.backend == 'grub': text += f' Profilo {result["profile"]}; attesa {result["timeout"]} s.'
            self.status.set(text)
        else:
            self.review = None; self.status.set(result['result'])
        self.buttons(); self.timer = self.window.after(100,self.poll)

    def close(self):
        if self.busy:
            self.status.set('Attendi la fine dell’operazione prima di chiudere.'); return
        self.window.after_cancel(self.timer)
        self.window.destroy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=('gui','plan','apply','restore'), default='gui')
    parser.add_argument('--backend', choices=('grub','limine'))
    parser.add_argument('--theme', choices=THEMES, default='synaptic-cosmos')
    parser.add_argument('--profile', choices=PROFILES, default='1080p')
    parser.add_argument('--timeout', type=int, choices=range(1,61), default=8)
    parser.add_argument('--expected-review')
    parser.add_argument('--approve-boot-write', action='store_true')
    parser.add_argument('--recovery-confirmed', action='store_true')
    args = parser.parse_args()
    try:
        if args.action == 'gui':
            if os.geteuid() == 0:
                raise RuntimeError('Avvia il selettore senza sudo; l’autenticazione arriva solo alle operazioni amministrative')
            try:
                import tkinter as tk
            except ImportError:
                raise RuntimeError('Manca Tk: installare python3-tk su Ubuntu/Debian oppure tk su Omarchy. I gestori CLI restano disponibili.')
            window = tk.Tk(); Wizard(window,BASE); window.mainloop()
        else:
            if not args.backend: parser.error('--backend richiesto per questa azione')
            print(json.dumps(operation(BASE,args),ensure_ascii=False))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr); sys.exit(1)


if __name__ == '__main__': main()
