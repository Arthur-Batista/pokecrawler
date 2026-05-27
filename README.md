# Poké-Crawler

Este projeto é um web crawler assíncrono desenvolvido para extrair informações detalhadas de Pokémon do portal Bulbapedia. O sistema realiza requisições de rede de forma concorrente, faz o parsing do HTML e normaliza os dados brutos em um banco de dados relacional.

## Arquitetura do Projeto (ETL)

A solução foi estruturada com forte separação de responsabilidades, dividindo o processo em três camadas principais:

1. **Extract (`fetcher.py`)**: Gerencia o I/O de rede. Responsável por realizar requisições HTTP e o download de mídias de forma não-bloqueante.
2. **Transform (`parser.py`)**: Isola a lógica do `BeautifulSoup` para navegar no DOM, localizar tags e aplicar a normalização de tipos de dados (ex: strings para inteiros). Caso algum campo esteja ausente no HTML, a falha é tratada silenciosamente (retornando `None`), garantindo que o pipeline não seja interrompido por páginas fora do padrão.
3. **Load (`storage.py`)**: Camada de persistência. Salva os dados transformados e as referências das imagens em um banco de dados SQLite local.

O arquivo `main.py` atua como o **Orquestrador**, despachando as tarefas e controlando o fluxo e a concorrência geral da aplicação.

## Decisões Técnicas e Ferramentas

Para atender ao requisito de concorrência e alto volume de dados, a arquitetura foi desenhada em torno do **Event Loop** do Python, garantindo o máximo aproveitamento de recursos (I/O Bound).

* **`asyncio` & `httpx`**: Em vez do tradicional `requests` (que é síncrono e bloquearia a execução), o `httpx` permite enviar múltiplas requisições simultâneas. O controle de tráfego é feito por um `asyncio.Semaphore`, evitando que o crawler sobrecarregue o servidor destino ou esgote as portas da máquina local.
* **`aiofiles`**: O download e salvamento das imagens no disco é feito de forma assíncrona. Isso impede que o I/O de disco gere gargalos nas requisições de rede.
* **`sqlite3` com `asyncio.Lock()`**: Como o SQLite não lida bem com escritas massivas concorrentes, implementei uma trava (Lock) que organiza o salvamento dos dados em uma fila indiana segura, evitando a corrupção do arquivo `.db`.
* **Resiliência**: O motor de extração conta com um mecanismo nativo de *retry*. Em caso de instabilidade de rede ou limite de requisições, o crawler aplica um tempo de espera exponencial antes de tentar novamente, garantindo resiliência sem adicionar bibliotecas extras complexas.
* **Logging**: O pipeline gera registros operacionais (terminal e arquivo `crawler.log`), criando uma trilha de auditoria essencial para monitoramento e debug em ambientes automatizados.

## 🚀 Como Executar

### 1. Pré-requisitos
Certifique-se de ter o Python 3.10+ instalado no seu sistema.

### 2. Configuração do Ambiente Virtual
Clone este repositório e crie um ambiente virtual para isolar as dependências:

```bash
# Criar o ambiente virtual
python3 -m venv venv

# Ativar o ambiente
source venv/bin/activate
```

### 3. Instalação das Dependências
Instale as bibliotecas necessárias contidas no projeto:
```bash 
pip install -r requirements.txt
 ```

### 4. Executando o Crawler
Com o ambiente ativado, basta iniciar o orquestrador:
```bash 
python main.py
 ```

Você poderá acompanhar o progresso das extrações em tempo real através do terminal e visualizar os logs detalhados no arquivo crawler.log gerado na raiz do projeto. As imagens serão salvas no diretório images/ e os dados consolidados no arquivo pokemons.db.

Desenvolvido de ❤️ por **Arthur Batista**.
