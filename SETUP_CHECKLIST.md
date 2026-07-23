# Yayınlamadan Önce

## Çerçeve değişti — artık "terk edilmiş" görünmüyor

```
ÖNCE : "Why I stopped"        → terk edilmiş proje sinyali
SONRA: "Known constraints"    → nötr teknik bilgi
       "Status: early stage"  → devam eden proje
       "Roadmap" (kutucuklu)  → açık kapı
```

Kısıtlar (depolama, ısınma) hâlâ yazıyor ama **bilgi olarak**, gerekçe olarak
değil. Ve son cümlesi ileriye bakıyor:

> It is what a 4B model costs on hardware built for a different job, and it
> will keep improving as both the runtimes and the chips do.

Roadmap'in ilk maddesi de "Benchmark and publish real throughput figures" —
yani sayının neden olmadığı belli ve ne zaman geleceği belli.

---

## Test: artık doğrulanmış bir şey var

`test_agent.py` eklendi. Android, model, llama.cpp gerekmiyor:

```bash
cd pocket-agent
python test_agent.py
```

Bende hepsi geçti:

```
1. Tool-call parser        5/5
2. Safety guards           4/4
3. File tools round-trip   1/1
4. Loop terminates         2/2
5. Tool then answer        2/2
6. Step cap                2/2
7. Fallback heuristic      2/2
```

Bunu kendi makinende bir kez çalıştır. Geçerse repo artık boş bir iddia
değil — loop'un çalıştığı doğrulanmış oluyor.

> `httpx` bile gerekmiyor; `agent.py`'de import tembelleştirildi.

---

## Senin PowerShell hataların

```powershell
llama-server -m <model>.gguf --port 8080
```
`<model>.gguf` bir yer tutucuydu, birebir yazınca PowerShell `<` karakterini
yönlendirme operatörü sanıyor. Zaten Windows'ta `llama-server` kurulu değilse
çalışmazdı. Gerek de yok — `test_agent.py` sunucusuz test ediyor.

```powershell
python agent.py --once "..."
```
`agent.py` o klasörde değildi. Önce repo klasörüne gir:

```powershell
cd C:\Users\armag\Downloads\pocket-agent
python test_agent.py
```

---

## Kalan işler

- [ ] `test_agent.py`'yi bir kez çalıştır, geçtiğini gör
- [ ] `<username>` yer tutucularını değiştir
- [ ] LICENSE (GitHub'da repo açarken MIT seç)

## Repo ayarları

```
Description : Tool-calling LLM agent for Android via Termux + llama.cpp —
              install path, a loop designed for small models, and honest
              notes on tablet hardware limits
Topics      : llm  android  termux  llama-cpp  on-device-ai  edge-ai
              qwen  local-llm  agent  tool-calling
```

## Commit

```bash
git init
git add .
git commit -m "Tool-calling LLM agent for Android via Termux + llama.cpp"
git branch -M main
git remote add origin https://github.com/<kullanıcı>/pocket-agent.git
git push -u origin main
```
