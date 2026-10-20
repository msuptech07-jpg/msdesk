# MSUPTECH_MSDESK_MARCA_V1 — aplica a marca MS Desk (MSuptech) no codigo do RustDesk antes de compilar.
# Roda no GitHub Actions (msdesk-windows.yml), na raiz do repositorio, com o submodulo hbb_common ja baixado.
# Toda troca e por texto literal e exige exatamente 1 ocorrencia: se o RustDesk mudar, a compilacao para aqui.
import os
import shutil

SERVIDOR = "acesso.msuptech.com.br"
CHAVE = "HUHArkVk79sGUYbDynknzpwKTU4xil+hazKN9TCTHvU="  # chave PUBLICA do nosso servidor (/opt/msuptech-rustdesk/data)
NOME = "MS Desk"

# cores: marinho MSuptech (botoes) e ambar do "DESK" da logo (destaques)
MARINHO = "0xFF22324F"
AZUL_ACAO = "0xFF2F5BA8"
AMBAR = "0xFFFFB547"


def troca(caminho, antes, depois):
    with open(caminho, encoding="utf-8") as f:
        texto = f.read()
    n = texto.count(antes)
    if n != 1:
        raise SystemExit(f"{caminho}: esperava 1 ocorrencia de {antes!r}, achei {n}")
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        f.write(texto.replace(antes, depois))
    print(f"ok {caminho}: {antes[:50]!r}")


# servidor, chave e nome do programa
cfg = "libs/hbb_common/src/config.rs"
troca(cfg, 'pub const RENDEZVOUS_SERVERS: &[&str] = &["rs-ny.rustdesk.com"];',
      f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{SERVIDOR}"];')
troca(cfg, 'pub const RS_PUB_KEY: &str = "OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw=";',
      f'pub const RS_PUB_KEY: &str = "{CHAVE}";')
troca(cfg, 'pub static ref APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
      f'pub static ref APP_NAME: RwLock<String> = RwLock::new("{NOME}".to_owned());')

# MSUPTECH_MSDESK_SEGURANCA_V1: padrao de seguranca de fabrica (o tecnico/cliente ainda pode mudar no proprio programa).
# - senha de uso unico de 8 caracteres com letras (muda a cada sessao, como AnyDesk/TeamViewer)
# - nao se anuncia na rede local e nao aceita conexao direta por IP (so pelo nosso servidor, com a nossa chave)
# - o tecnico nao altera as configuracoes do cliente a distancia
# - desconecta sozinho apos 10 min sem uso
# - nao oferece "atualizar" para o RustDesk oficial (perderia a marca e o servidor)
PADRAO = {
    "verification-method": "use-temporary-password",
    "temporary-password-length": "8",
    "allow-numeric-one-time-password": "N",
    "enable-lan-discovery": "N",
    "direct-server": "N",
    "allow-remote-config-modification": "N",
    "allow-auto-disconnect": "Y",
    "auto-disconnect-timeout": "10",
    "enable-check-update": "N",
}
itens = ", ".join(f'("{k}", "{v}")' for k, v in PADRAO.items())
troca(cfg, "pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = Default::default();",
      "pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(\n"
      f"        [{itens}]\n"
      "            .iter().map(|(k, v)| (k.to_string(), v.to_string())).collect());")

# nome que o Windows mostra (propriedades do arquivo, gerenciador de tarefas, barra de tarefas)
rc = "flutter/windows/runner/Runner.rc"
troca(rc, 'VALUE "CompanyName", "Purslane Tech Pte. Ltd." "\\0"', 'VALUE "CompanyName", "MSuptech" "\\0"')
troca(rc, 'VALUE "FileDescription", "RustDesk Remote Desktop" "\\0"', f'VALUE "FileDescription", "{NOME} - Acesso remoto MSuptech" "\\0"')
troca(rc, 'VALUE "ProductName", "RustDesk" "\\0"', f'VALUE "ProductName", "{NOME}" "\\0"')
for toml in ("Cargo.toml", "libs/portable/Cargo.toml"):
    troca(toml, 'ProductName = "RustDesk"', f'ProductName = "{NOME}"')
    troca(toml, 'FileDescription = "RustDesk Remote Desktop"', f'FileDescription = "{NOME} - Acesso remoto MSuptech"')

# cores do programa
dart = "flutter/lib/common.dart"
troca(dart, "static const Color accent = Color(0xFF0071FF);", f"static const Color accent = Color({AZUL_ACAO});")
troca(dart, "static const Color accent50 = Color(0x770071FF);", "static const Color accent50 = Color(0x772F5BA8);")
troca(dart, "static const Color accent80 = Color(0xAA0071FF);", "static const Color accent80 = Color(0xAA2F5BA8);")
troca(dart, "static const Color idColor = Color(0xFF00B6F0);", f"static const Color idColor = Color({AMBAR});")
troca(dart, "static const Color button = Color(0xFF2C8CFF);", f"static const Color button = Color({MARINHO});")

# icones e logo
marca = "msdesk/marca"
copias = {
    "icon.ico": ["res/icon.ico", "res/tray-icon.ico", "flutter/windows/runner/resources/app_icon.ico"],
    "icon.png": ["res/icon.png", "flutter/assets/icon.png"],
    "logo_dark.png": ["flutter/assets/logo_dark.png"],
    "logo_light.png": ["flutter/assets/logo_light.png"],
}
for origem, destinos in copias.items():
    o = os.path.join(marca, origem)
    if not os.path.exists(o):
        raise SystemExit(f"falta {o}")
    for d in destinos:
        shutil.copyfile(o, d)
        print(f"ok copiado {o} -> {d}")
# MSUPTECH_MSDESK_ANDROID_V1 — Android: nome, identificador proprio (instala separado do RustDesk oficial), cor e icones
app = "flutter/android/app"
troca(f"{app}/build.gradle", 'applicationId "com.carriez.flutter_hbb"', 'applicationId "com.msuptech.msdesk"')
man = f"{app}/src/main/AndroidManifest.xml"
troca(man, 'android:label="RustDesk"', f'android:label="{NOME}"')
troca(man, 'android:label="RustDesk Input"', f'android:label="{NOME} Input"')
strings = f"{app}/src/main/res/values/strings.xml"
troca(strings, '<string name="app_name">RustDesk</string>', f'<string name="app_name">{NOME}</string>')
troca(strings, "when RustDesk screen sharing is established", f"when {NOME} screen sharing is established")
troca(strings, "Keeps the RustDesk remote desktop host available", f"Keeps the {NOME} remote desktop host available")
kt = f"{app}/src/main/kotlin/com/carriez/flutter_hbb"
troca(f"{kt}/MainService.kt", 'const val DEFAULT_NOTIFY_TITLE = "RustDesk"', f'const val DEFAULT_NOTIFY_TITLE = "{NOME}"')
troca(f"{kt}/MainService.kt", 'val channelName = "RustDesk Service"', f'val channelName = "{NOME}"')
troca(f"{kt}/BootReceiver.kt", 'Toast.makeText(context, "RustDesk is Open", Toast.LENGTH_LONG)', f'Toast.makeText(context, "{NOME} aberto", Toast.LENGTH_LONG)')
troca(f"{app}/src/main/res/values/colors.xml", '<color name="primary">#FF0071FF</color>', '<color name="primary">#FF2F5BA8</color>')
for xml in ("ic_launcher.xml", "ic_launcher_round.xml"):
    p = f"{app}/src/main/res/mipmap-anydpi-v26/{xml}"
    troca(p, '<background android:drawable="@color/ic_launcher_background"/>', '<background android:drawable="@mipmap/ic_launcher_bg"/>')
    troca(p, '<monochrome android:drawable="@mipmap/ic_launcher_foreground"/>', '<monochrome android:drawable="@mipmap/ic_launcher_monochrome"/>')
for dens in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"):
    o = os.path.join(marca, "android", f"mipmap-{dens}")
    for arq in os.listdir(o):
        shutil.copyfile(os.path.join(o, arq), f"{app}/src/main/res/mipmap-{dens}/{arq}")
    print(f"ok icones android mipmap-{dens}")
print("marca MS Desk aplicada")
