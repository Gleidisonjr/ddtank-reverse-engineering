# Engenharia Reversa do Pacote de UI PickGliss (xml.png) — DDTank / 7Road

## Contexto & Sintoma
No carregamento do cliente desktop do DDTank Clássico (DDClassico.com / motor 7Road v2.0.5), após superar a tela preta com a correção do `config.xml` e da rotação de Splash Art, o preloader travava invariavelmente em **33%** com requisições HTTP retornando código 404:
```
GET /flash/1.png?... 200
GET /flash/ui//xml/xml.png?lv=-1 404 - File not found
GET /flash/ui//xml/xml.png?lv=-1 404 - File not found
```

## Análise de Bytecode AVM2 & Descobertas

### 1. Obtenção do Caminho (`ComponentSetting.as`)
A descompilação do bloco ABC no `1.swf` e `Loading.swf` revelou o método `com.pickgliss.ui:ComponentSetting/getUIConfigZIPPath`:
```actionscript
public static function getUIConfigZIPPath():String {
    return ComponentSetting.FLASHSITE + "ui/" + ComponentSetting.LANGUAGE + "/xml/xml.png";
}
```
Como a variável `LANGUAGE` não estava configurada (`""`), o cliente requisitou o path com barra dupla: `/flash/ui//xml/xml.png`.

### 2. O Formato de `xml.png`: Arquivo FZip Disfarçado
Ao inspecionar o manipulador de carregamento em `com.pickgliss.loader:UIModuleLoader`:
- Método 880 (`__onLoadZipComplete`): obtém o `content` binário retornado do download.
- Método 883 (`hasHead`): verifica se há o cabeçalho obfuscador proprietário da 7Road (`road7` ou `swf_head`). Se presente, remove o cabeçalho; se ausente, trata o payload como arquivo ZIP padrão.
- Método 885 (`__onZipParaComplete`):
```actionscript
var count:int = zip.getFileCount();
for (var i:int = 0; i < count; i++) {
    var file:FZipFile = zip.getFileAt(i);
    var xmlStr:String = file.content.toString();
    var xml:XML = new XML(xmlStr);
    ComponentFactory.Instance.setup(xml);
}
this._zipLoadComplete = true;
this.loadNextModule();
```
Comprovou-se empiricamente que `xml.png` **NÃO é uma imagem PNG estática**, mas sim um arquivo **ZIP (`PK\x03\x04`)** empacotado com a extensão `.png` contendo as definições de componentes UI (`core.xml`) para o `ComponentFactory`.

### 3. O Parser do `ComponentFactory` e `ComponentModel`
No método `ComponentModel::paras`:
- Lê `<custom>` -> armazena em `_customObjectStyle[stylename]`
- Lê `<component>` -> armazena em `_componentStyle[stylename]`
- Lê `<tips>` -> armazena em `_allTipStyles`
- Lê `<set>` -> armazena em `_styleSets`
- Lê `<bitmap>` -> armazena em `_bitmapSets`
- Lê `<bitmapData>` -> armazena em `_bitmapDataSets`

Com a ausência do arquivo no CDN local, o `UIModuleLoader` nunca disparava o evento `_zipLoadComplete = true`, bloqueando o pipeline de carga exatamente no milestone de 33%.

## Solução Implementada

1. **Gerador de Assets (`tools/generate_ui_xml_png.py`)**:
   - Cria dinamicamente um arquivo ZIP comprimido contendo `core.xml` com as definições de fontes tipográficas (`defaultFont`), alertas (`SimpleAlert`, `TimeoutAlert`) e molduras padrão (`core.Frame`).
   - Salva o arquivo em `www/flash/ui/xml/xml.png` e `www/ui/xml/xml.png`.

2. **Servidor CDN Local (`src/ddt_local_cdn.py`)**:
   - Sanitização de barras duplas (`//` -> `/`).
   - Roteamento explícito para servir `xml.png` com MIME `image/png` (ou `application/octet-stream`).
   - Fallback de segurança para requisições de imagens não mapeadas retornando PNG transparente de 1x1.
