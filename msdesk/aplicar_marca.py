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
# MSUPTECH_MSDESK_NOME_INTERNO_V1: no Windows o nome interno nao pode ter espaco (o instalador exige [a-zA-Z0-9-]+;
# com "MS Desk" a instalacao falhava e a janela fechava). O workflow do Windows passa MSDESK_APP_NAME=MSDesk;
# o Android segue "MS Desk" (la nao tem esse instalador e mudar o nome trocaria o ID do celular).
NOME_INTERNO = os.environ.get("MSDESK_APP_NAME", NOME)
troca(cfg, 'pub static ref APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
      f'pub static ref APP_NAME: RwLock<String> = RwLock::new("{NOME_INTERNO}".to_owned());')

# MSUPTECH_MSDESK_SEGURANCA_V1: padrao de seguranca de fabrica (o tecnico/cliente ainda pode mudar no proprio programa).
# - senha de uso unico de 8 caracteres com letras (muda a cada sessao, como AnyDesk/TeamViewer)
# - nao se anuncia na rede local e nao aceita conexao direta por IP (so pelo nosso servidor, com a nossa chave)
# - o tecnico nao altera as configuracoes do cliente a distancia
# - NAO desconecta por inatividade (MSUPTECH_MSDESK_SEM_INATIVIDADE_V1, Marcus 28/10: "fechou minha conexao, isso
#   nao pode acontecer"; quem quer limite usa o botao Tempo de sessao)
# - nao oferece "atualizar" para o RustDesk oficial (perderia a marca e o servidor)
PADRAO = {
    "verification-method": "use-temporary-password",
    "temporary-password-length": "8",
    "allow-numeric-one-time-password": "N",
    "enable-lan-discovery": "N",
    "direct-server": "N",
    "allow-remote-config-modification": "N",
    "allow-auto-disconnect": "N",
    "auto-disconnect-timeout": "10",
    "enable-check-update": "N",
}
itens = ", ".join(f'("{k}", "{v}")' for k, v in PADRAO.items())
troca(cfg, "pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = Default::default();",
      "pub static ref DEFAULT_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(\n"
      f"        [{itens}]\n"
      "            .iter().map(|(k, v)| (k.to_string(), v.to_string())).collect());")

# MSUPTECH_MSDESK_TELA_AJUSTADA_V1: no computador, a tela remota abre AJUSTADA A JANELA e com barra de rolagem manual.
# Antes abria no tamanho original com "rolagem automatica": a tela de celular (comprida) passava da janela e ia
# rolando sozinha acompanhando o mouse (reclamacao do Marcus 20/10).
troca(cfg, 'keys::OPTION_VIEW_STYLE => self.get_string(key, "original", vec!["adaptive"]),',
      'keys::OPTION_VIEW_STYLE => self.get_string(key, "adaptive", vec!["original"]),')
troca(cfg, 'self.get_string(key, "scrollauto", vec!["scrolledge", "scrollbar"])',
      'self.get_string(key, "scrollbar", vec!["scrollauto", "scrolledge"])')

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
    # MSUPTECH_MSDESK_TITULO_V2: logo do topo do app no celular (M + "MS" originais + "Desk")
    "msdesk_titulo.png": ["flutter/assets/msdesk_titulo.png"],
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
# MSUPTECH_MSDESK_DESEMPENHO_V1: "lento e imagem ruim" (Marcus 20/10). Tres travas do RustDesk que so liberam o
# desempenho cheio no servidor PUBLICO dele (rustdesk.com); no nosso servidor ficavam ligadas:
# 1) using_public_server(): como o nosso servidor vai fixo no codigo (nao na opcao "custom-rendezvous-server"), o
#    programa se achava no servidor publico e limitava imagem personalizada a 50 e fps a 30 quando a conexao passa
#    pelo repasse. Aqui nunca e publico.
troca("src/common.rs",
      'crate::get_custom_rendezvous_server(get_option("custom-rendezvous-server")).is_empty()',
      "false")
# 2) punch UDP e IPv6 vinham DESLIGADOS por padrao fora do servidor publico (get_local_option devolvia "N"): sem eles a
#    conexao direta (ponto a ponto) quase nunca fecha e tudo vai pelo repasse da VPS. Nosso hbbs ja trata o punch UDP.
#    WebRTC segue desligado (precisa de servidor STUN/ICE que nao temos).
troca("src/common.rs",
      '            if !is_public(&Config::get_rendezvous_server()) {\n                return "N".to_owned();\n            }',
      '            if key == keys::OPTION_ENABLE_WEBRTC {\n                return "N".to_owned();\n            }\n            return "Y".to_owned();')
# 3) padrao de imagem: qualidade personalizada 80 (o "equilibrado" sem escolha ficava em ~50) e 60 fps quando o
#    aparelho nao escolheu (antes 30). A rede/CPU ainda reduzem sozinhas (QoS adaptativo do RustDesk).
troca(cfg, "pub static ref DEFAULT_DISPLAY_SETTINGS: RwLock<HashMap<String, String>> = Default::default();",
      "pub static ref DEFAULT_DISPLAY_SETTINGS: RwLock<HashMap<String, String>> = RwLock::new(\n"
      '        [("image_quality", "custom"), ("custom_image_quality", "80")]\n'
      "            .iter().map(|(k, v)| (k.to_string(), v.to_string())).collect());")
troca("src/client.rs",
      'if let Some(custom_fps) = self.options.get("custom-fps") {\n                let mut custom_fps = custom_fps.parse().unwrap_or(30);',
      'if let Some(custom_fps) = self.options.get("custom-fps").cloned().or_else(|| Some("60".to_owned())) {\n                let mut custom_fps = custom_fps.parse().unwrap_or(60);')

print("marca MS Desk aplicada")
