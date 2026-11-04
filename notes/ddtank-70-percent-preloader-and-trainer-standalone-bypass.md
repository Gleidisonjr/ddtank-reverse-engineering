# Engenharia Reversa do Preloader 70% e Bypass do Trainer Standalone — DDTank 7Road

## 1. Contexto & Sintoma
Após a resolução da tela preta e do travamento em 33% (`xml.png`), o cliente desktop do DDTank Clássico (DDClassico.com / motor 7Road v2.0.5) progrediu até a marca de **70%** na barra de carregamento e congelou indefinidamente com as seguintes requisições no console do servidor:

```
127.0.0.1 - - [03/Nov/2026 20:18:49] "GET /flash/1.png?... HTTP/1.1" 200 -
127.0.0.1 - - [03/Nov/2026 20:18:49] "GET /flash/ui//xml/xml.png?lv=-1 HTTP/1.1" 200 -
127.0.0.1 - - [03/Nov/2026 20:18:49] "GET /flash/ui//swf/choicefigure.swf?lv=-1 HTTP/1.1" 404 -
127.0.0.1 - - [03/Nov/2026 20:18:49] "GET /flash/ui//swf/choicefigure.swf?lv=-1 HTTP/1.1" 404 -
127.0.0.1 - - [03/Nov/2026 20:18:49] "GET /flash/ui//swf/roadcomponent.swf?lv=-1 HTTP/1.1" 404 -
127.0.0.1 - - [03/Nov/2026 20:18:49] "GET /flash/ui//swf/roadcomponent.swf?lv=-1 HTTP/1.1" 404 -
127.0.0.1 - - [03/Nov/2026 20:18:49] "GET /flash/3.png?rn=0.6174027668312192 HTTP/1.1" 200 -
```

---

## 2. Análise de Bytecode AVM2 & Diagnóstico

### 2.1 Falhas de Módulos de Interface (404)
No bytecode de `Loading.swf` (`RegisterLuncher.as`):
- O carregamento da primeira etapa (código de registro `1.png` / `1.swf`) avança o progresso até ~33%.
- Em seguida, o `RegisterLuncher` invoca:
  ```actionscript
  UIModuleLoader.Instance.addUIModuleImp("choicefigure");
  UIModuleLoader.Instance.addUIModuleImp("roadcomponent");
  ```
- O cálculo do path computa `FLASHSITE + "ui/" + LANGUAGE + "/swf/" + name + ".swf"`. Como `LANGUAGE` não está configurado, o caminho vira `/flash/ui//swf/choicefigure.swf` e `/flash/ui//swf/roadcomponent.swf`.
- O servidor local retornava HTTP 404 para esses arquivos, disparando tentativas duplicadas do loader e retenção de estado.

### 2.2 O Congelamento Fatal em `3.png`
No bytecode de `1.swf` (`register.view:MainFigureView/tryEnter`):
```actionscript
if (RegisterState.TrainerStandalone) {
    this.enterTrain();
    this.dispose();
} else {
    this.addMainLoading();
    this.enterGame();
    this.dispose();
}
```
1. No `config.xml`, a tag `<TRAINER_STANDALONE value="true">true</TRAINER_STANDALONE>` estava ativa.
2. Isso forçou o cliente a executar `enterTrain()`.
3. `enterTrain()` requisitou `FLASHSITE + "3.png"` (`TrainPath = "3.png"`).
4. No ecossistema 7Road:
   - `1.png` = SWF comprimido contendo `RegisterState` e fluxo inicial de boot.
   - `2.png` = SWF comprimido contendo o núcleo principal do DDTank (`ddt.DDT`).
   - `3.png` = SWF comprimido contendo o módulo Trainer (Treinamento / Tutorial).
5. Como `3.png` não existia no diretório `www/flash/`, o servidor CDN ativava o fallback genérico de imagens e servia um **PNG transparente de 1x1 de 67 bytes**.
6. O Flash Player recebia os bytes da imagem PNG e tentava carregá-los via `Loader.loadBytes(bytes)` esperando bytecode AVM2 compilado. Ao falhar silenciosamente no parser SWF interno, o fluxo de execução travava exatamente em **70%**.

---

## 3. Solução Cirúrgica Implementada

### 3.1 Desativação de `TRAINER_STANDALONE` no `config.xml`
Ambas as instâncias (no nó interno `<config><config>` e no nó raiz) foram alteradas para:
```xml
<TRAINER_STANDALONE value="false">false</TRAINER_STANDALONE>
```
Com isso, `MainFigureView.tryEnter` desvia imediatamente para:
```actionscript
this.addMainLoading();
this.enterGame();
```
`enterGame()` chama `GameLuncher.loadCore()`, que requisita diretamente `2.png` (o core real do jogo de 3.23 MB já presente em disco).

### 3.2 Geração de SWFs Válidos Mínimos em AS3
Criado o script [`projects/ddtank-server/tools/generate_dummy_swfs.py`](file:///C:/Users/dopamine/Desktop/Projetos/Reverse%20Engineering/projects/ddtank-server/tools/generate_dummy_swfs.py), construindo SWFs de 31 bytes compatíveis com Flash Player 14:
- Cabeçalho `FWS\x0e` com tamanho 31 bytes.
- Dimensões TWIPS (800x600 px).
- Tag 69 (`FileAttributes`) com bit 3 ativo (`0x08` = ActionScript 3).
- Tag 1 (`ShowFrame`) e Tag 0 (`End`).

Arquivos gerados:
- `www/flash/ui/swf/choicefigure.swf`
- `www/flash/ui/swf/roadcomponent.swf`
- `www/ui/swf/choicefigure.swf`
- `www/ui/swf/roadcomponent.swf`
- `www/flash/3.png` (SWF válido para proteção contra chamadas ao tutorial)

### 3.3 Fallback Dinâmico no CDN Local (`ddt_local_cdn.py`)
- Resolução de caminhos duais (com ou sem `/flash/`).
- Se qualquer `.swf` requisitado não existir em disco, o CDN serve imediatamente o SWF AS3 mínimo com `Content-Type: application/x-shockwave-flash` (eliminando 404s em módulos de UI opcionais).
- Roteamento dedicado para `3.png` garantindo retorno de SWF válido.

### 3.4 Configuração de IP do Servidor em `ServerList.xml`
Adicionado explicitamente `IP="127.0.0.1"` e `ID="1"` no `<Item ...>` do `ServerList.xml`, impedindo o fallback para o IP padrão hardcoded da 7Road (`40.160.19.199`).
