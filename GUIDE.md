# Guia Completo: Tradução DBI 849 do Russo para Português

## Objetivo
Traduzir o DBI 849 do russo para o português, superando as incompatibilidades introduzidas na versão 846+ devido a mudanças no sistema de geração de chaves.

---

## PASSO 1: Extrair Todas as Chaves do DBI 849

### Comando:
```bash
./bin/dbipatcher --find-keys --nro dbi/DBI.849.ru.nro > keys.849.txt
```

### O que faz:
- Extrai **todas** as 4389 chaves de criptografia do binário DBI 849
- Salva em `keys.849.txt`

### Resultado esperado:
```
Arquivo criado: keys.849.txt (~4389 linhas)
```

---

## PASSO 2: Escanear Strings Russas no DBI 849

### Comando:
```bash
sh -c "./bin/dbipatcher --new-ru --nro dbi/DBI.849.ru.nro --min 2 --keys 4389 --keygen keys.849.txt --dict translate/dict.txt > translate/new_ru_849.txt"
```

### O que faz:
- Usa as 4389 chaves para escanear o NRO
- Procura strings em russo (cirílico) com mínimo 2 caracteres
- Compara com o dicionário existente para evitar duplicatas
- Salva todas as strings encontradas

### Resultado esperado:
```
Arquivo criado: translate/new_ru_849.txt
Contém ~6269 strings russas válidas com seus key indexes
Exemplo de linha:
   at 0x00630080 key 0x2d4d67d92189732f / 1        [53 ]: 'Невозможно разобрать content meta'
```

---

## PASSO 3: Remapear Dicionário

### Comando:
```bash
python remap_dictionary.py
```

### O que faz:
- Lê `translate/new_ru_849.txt` (strings encontradas no DBI 849)
- Lê `translate/dict.txt` (dicionário original do DBI 845)
- Para cada entrada do dicionário, procura o texto no scan do 849
- Se encontrar, atualiza o key index para o valor do DBI 849
- Salva em `translate/dict.849.txt`

### Resultado esperado:
```
Arquivo criado: translate/dict.849.txt
Saída do script:
  Found 6269 valid Russian strings with keys.
  Found 1431 dictionary entries.
  Generated dictionary: 1076 found, 355 missing.
```

**Observação:** O script `remap_dictionary.py` deve ter esta configuração:
```python
def main():
    new_ru_path = "translate/new_ru_849.txt"  # ← Usar este arquivo
    dict_path = "translate/dict.txt"
    output_path = "translate/dict.849.txt"
```

---

## PASSO 4: Criar Dicionário Limpo (Apenas Entradas Mapeadas)

### Comando:
```bash
python -c "with open('translate/dict.849.txt', 'r', encoding='utf-8') as f, open('translate/dict.849_clean.txt', 'w', encoding='utf-8', newline='\n') as out: [out.write(line) for line in f if not line.startswith('// MISSING')]"
```

### O que faz:
- Remove todas as linhas que começam com `// MISSING`
- Mantém apenas as entradas que foram mapeadas com sucesso
- Garante encoding UTF-8 com line endings Unix

### Resultado esperado:
```
Arquivo criado: translate/dict.849_clean.txt
Formato: ID;KeyIndex;TextoRusso
Exemplo:
ACT024;22;Невозможно прочитать общие тикеты
CV024;18;Просмотр раздела SYSTEM
...
```

---

## PASSO 5: Gerar Blueprint

### Comando:
```bash
./bin/dbipatcher --scan --nro dbi/DBI.849.ru.nro --dict translate/dict.849_clean.txt --out translate/blueprints/blueprint.849.txt --keygen keys.849.txt
```

### O que faz:
- Escaneia o NRO usando o dicionário remapeado
- **USA TODAS AS 4389 CHAVES**
- Procura cada string do dicionário no binário
- Para cada match, identifica os endereços de memória onde a string aparece
- Gera um "blueprint" com instruções de patch

### Resultado esperado:
```
Arquivo criado: translate/blueprints/blueprint.849.txt
Exemplo de saída do comando:
  loaded 1076 references
  matched_full:      940
  matched_partial:   5
  unmatched_long:    0
  duplicates:        131
```

---

---

## PASSO 6: Aplicar Patch

### Comando:
```bash
./bin/dbipatcher --patch translate/blueprints/blueprint.849.txt --nro dbi/DBI.849.ru.nro --lang translate/lang.br.txt --out dbi/DBI.849.br.nro
```

### O que faz:
- Lê o blueprint (instruções de onde patchear)
- Lê o arquivo de tradução (o que substituir)
- Aplica as substituições no NRO original
- Gera novo NRO com strings em português

### Resultado esperado:
```
Arquivo criado: dbi/DBI.849.br.nro
Saída do comando:
  Patching completed successfully
  940+ strings replaced
```

## Resumo dos Arquivos Gerados

```
keys.849.txt              → Todas as 4389 chaves extraídas
translate/new_ru_849.txt      → strings russas encontradas no DBI 849
translate/dict.849.txt        → Dicionário remapeado completo (1076 + 355 missing)
translate/dict.849_clean.txt  → Dicionário remapeado (só 1076 mapeados)
translate/blueprints/blueprint.849.txt   → Blueprint para patch (940 matches)
translate/lang.br.txt          → Traduções em português
dbi/DBI.849.br.nro            → NRO final patcheado
```

---

## Diferença Entre DBI 845 e DBI 849

| Aspecto | DBI 845 | DBI 849 |
|---------|---------|---------|
| **Sistema de Chaves** | MurmurHash3 | Array extraído do binário |
| **Número de Chaves** | Calculadas dinamicamente | 4389 chaves fixas |
| **Compatibilidade** | Dicionário antigo funciona | Requer remapeamento |
| **Key Index** | Baseado em hash | Baseado em posição no array |


## Exemplos de Comandos

```bash

#Procurar Strings
./bin/dbipatcher --find-str "cохранения" --nro dbi/DBI.849.br.nro --keys 4389 --keygen keys.849.txt

#Procurar immediates
./bin/dbipatcher --keys 4389 --keygen keys.849.txt --nro dbi/DBI.849.ru.nro --find-imm "Имя"

#Decodificar offset
./bin/dbipatcher --decode 0x00627b20 --nro dbi/DBI.849.br.nro --keys 4389 --keygen keys.849.txt

# PASSO 1: Extrair chaves
./bin/dbipatcher --find-keys --nro dbi/DBI.849.ru.nro > keys.849.txt

# PASSO 2: Escanear strings russas
sh -c "./bin/dbipatcher --new-ru --nro dbi/DBI.849.ru.nro --min 2 --keys 4389 --keygen keys.849.txt --dict translate/dict.txt > translate/new_ru_849-11.txt"

# PASSO 2.1: Escanear strings inglês
sh -c "./bin/dbipatcher --new-en --nro dbi/DBI.849.ru.nro --min 2 --keys 4389 --keygen keys.849.txt --dict translate/dict.txt > translate/new_en_849-8.txt"

# PASSO 3: Remapear dicionário
python remap_dictionary.py

# PASSO 4: Criar dicionário limpo
python -c "with open('translate/dict.849.txt', 'r', encoding='utf-8') as f, open('translate/dict.849_clean.txt', 'w', encoding='utf-8', newline='\n') as out: [out.write(line) for line in f if not line.startswith('// MISSING')]"

# PASSO 5: Gerar blueprint
./bin/dbipatcher --scan --nro dbi/DBI.849.ru.nro --dict translate/dict.849_clean.txt --out translate/blueprints/blueprint.849.txt --keygen keys.849.txt

# PASSO 6: Criar traduções (manual)

# Editar translate/lang.br.txt

# PASSO 7: Aplicar patch
./bin/dbipatcher --patch translate/blueprints/blueprint.849.txt --nro dbi/DBI.849.ru.nro --lang translate/lang.br.txt --out dbi/DBI.849.br.nro

```
---

---
Para quem desejar continuar o trabalho:
---

- Basta procurar mais strings e adicioná-las ao `dict.849_clean.txt` bem como suas traduções no `lang.br.txt`

---
Para quem desejar adaptar a tradução para outro idioma:
---

- Basta traduzir o arquivo `lang.br.txt`. para o seu idioma e executar os comandos para geração do blueprint/patch.
- Foi mantido o mesmo padrão de `Label=textoTraduzido`, então projetos de tradução paralelos podem facilmente adaptar

## Considerações

* Assim como nas versões traduzidas anteriormente, algumas funções podem não funcionar como o esperado.
* Com meu trabalho isolado acredito ter conseguido traduzir cerca de ~90% dos textos, mas ainda restam strings em russo.
* Com isso decidi publicar minhas descobertas da forma como estão.

## Agradecimentos

* [Morce3232](https://github.com/Morce3232) por disponibilizar esta ferramenta.
* [CostelaCNX](https://github.com/CostelaCNX) por ajudar a testar a tradução.
