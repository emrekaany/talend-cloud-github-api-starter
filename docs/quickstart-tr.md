# Türkçe hızlı başlangıç: Talend API + GitHub API CLI

Bu repo, Talend operasyon metadata'sını ve Talend Studio proje yapısını salt okunur biçimde incelemek için geliştirilmiş bağımsız bir Python komut satırı aracıdır. Qlik ile bağlantılı, Qlik tarafından desteklenen veya onaylanan resmî bir ürün değildir.

`talend-api`, bu repoya ait komuttur; Qlik'in ayrı **Talend CommandLine** ürünü değildir.

## İki dakikalık güvenli demo

Python 3.10+ ile yayınlanmış `v0.2.0` kaynak paketini doğrudan GitHub'dan
yalıtılmış bir ortama kur:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "https://github.com/emrekaany/talend-cloud-github-api-starter/archive/refs/tags/v0.2.0.zip"
talend-api demo
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install "https://github.com/emrekaany/talend-cloud-github-api-starter/archive/refs/tags/v0.2.0.zip"
talend-api demo
```

İlk kurulum Python paketlerini indirebilir. `demo` ise yalnız paket içindeki tamamen sentetik API yanıtlarını ve `.item` / `.properties` örneklerini kullanır. `demo-output/local_view.json` ile `demo-output/share_safe.json` dosyalarını yazar; Talend veya GitHub API'sine istek atmaz, hesap ya da token istemez.

Dokümanları ve örnekleri de yerelde tutmak istersen repoyu klonlayıp normal
kurulum yap:

```bash
git clone https://github.com/emrekaany/talend-cloud-github-api-starter.git
cd talend-cloud-github-api-starter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
talend-api demo
```

`python -m pip install -e .` yalnız kaynak kodu değiştirecek katkıcılar içindir.

## Komut haritası

```text
talend-api demo
talend-api local jobs PATH --path-prefix process
talend-api github jobs OWNER/REPOSITORY --ref main --path-prefix path/to/project/process
talend-api talend workspaces
talend-api talend tasks --help
talend-api talend runs --help
```

## Yerel Talend Studio projesini incele

Sahibi olduğun veya inceleme yetkin bulunan bir proje kökünü seç:

```bash
talend-api local jobs /path/to/TALEND_PROJECT \
  --path-prefix process
```

Bu akış ağ bağlantısı ve token gerektirmez. Seçilen kapsam altındaki desteklenen `.properties` / `.item` adaylarını okur; SQL, Java, shell, mapper ifadesi veya Talend job'ı çalıştırmaz. Gerçek müşteri veya işveren dosyasını, üretilen çıktıyı ya da yerel yolu public issue'a ekleme.

## Public GitHub reposunu anonim incele

Yetkili olduğun bir public repo ve dar bir Talend proje yolu kullan:

```bash
talend-api github jobs OWNER/REPOSITORY \
  --ref main \
  --path-prefix path/to/talend-project/process
```

Araç ref'i değişmez bir commit SHA'ya sabitler ve yalnız sınırlı `.item` / `.properties` metadata'sını okur. Repoyu klonlamaz, kodunu çalıştırmaz ve private repo token'ı kabul etmez. Ayrıntı: [GitHub API akışı](github-api.md).

Kurulumdan sonra credentialsız public self-test:

```bash
talend-api github jobs emrekaany/talend-cloud-github-api-starter \
  --ref refs/tags/v0.2.0 \
  --path-prefix examples/fixtures \
  --output-dir github-self-test
```

GitHub'ın güncel anonim limiti kaynak IP başına saatte 60 REST isteğidir; bu
CLI tek taramada en fazla 40 istek yapar. Paylaşılan ağdaki başka kullanım da
aynı provider kotasını tüketmiş olabilir. Yayındaki `v0.2.0`, geçici
`502`/`503`/`504` yanıtında otomatik retry yapmadan güvenli biçimde durur.
Güncel `v0.2.1` kaynak sürümü aynı bütçe içinde en fazla iki retry ekler; iki
sürüm de eksik sonucu başarılı göstermez.

## Talend API'yi kendi hesabınla kullan

Talend API bölgesel olarak şu biçimdeki hostta sunulur:

```text
https://api.<region>.cloud.talend.com
```

Bu ücretsiz repo sana Talend hesabı, lisans/trial, PAT, SAT, rol veya endpoint yetkisi vermez. Canlı komutlar için kendi yetkili hesabının güncel hostunu ve desteklenen credential türünü [Talend API kurulumuna](talend-api.md) göre yerel environment variable olarak tanımlamalısın. Token'ı komut satırı argümanına yazma.

```bash
talend-api talend workspaces
talend-api talend tasks --help
talend-api talend runs --help
```

Otomatik testler sentetik fixture ve mock HTTP transport kullanır; gerçek bir Talend tenant'ına login olunduğunu veya senin subscription/rol/endpoint yetkinin çalıştığını kanıtlamaz.

## Kesin sınırlar

- Task başlatma/durdurma, publish, update, delete veya upload yoktur.
- Business row data, ham log, ham XML ve context/connection değeri dışa aktarılmaz.
- Private GitHub repo authentication bu başlangıç paketinde yoktur.
- Public issue'a token, client dosyası, log, private repo URL'si, live tenant/workspace/run ID'si ya da gerçek `.item` / `.properties` içeriği koyma.

Daha fazla bilgi: [yetenek matrisi](supported-capabilities.md), [güvenlik modeli](security-model.md) ve [sorun giderme](troubleshooting.md).
