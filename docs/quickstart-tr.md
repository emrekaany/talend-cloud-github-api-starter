# Türkçe hızlı başlangıç

Bu bağımsız proje, Qlik Talend Cloud® ve Talend® Studio metadata'sı için salt okunur bir Python başlangıç paketidir; Qlik ile bağlantılı, Qlik tarafından desteklenen veya onaylanan resmî bir ürün değildir.

## İki dakikalık güvenli demo

Python 3.10+ ile repo klasöründe:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
talend-api-starter demo
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
talend-api-starter demo
```

İlk kurulum Python paketlerini indirebilir. `demo` komutu ise paket içindeki tamamen sentetik cloud yanıtlarını ve `.item` / `.properties` fixture'larını kullanır; `demo-output/local_view.json` ve `demo-output/share_safe.json` dosyalarını yazar. Talend Cloud veya GitHub API'sine istek atmaz, hesap ya da token istemez.

## Public GitHub reposunu incele

Yetkili olduğun bir public repo ve dar bir Talend proje yolu kullan:

```bash
talend-api-starter github jobs OWNER/REPOSITORY \
  --ref main \
  --path-prefix path/to/talend-project/process
```

Araç ref'i değişmez bir commit SHA'ya sabitler; yalnız sınırlı `.item` / `.properties` metadata'sını okur. Kodu, SQL'i, Java'yı veya shell ifadelerini çalıştırmaz. Ayrıntı: [GitHub API akışı](github-api.md).

## Talend Cloud canlı modu

Token'ı komut satırına yapıştırma. [Talend Cloud API kurulumundaki](talend-cloud-api.md) yerel ortam değişkenlerini ve hesabına ait tam HTTPS API hostunu kullan, ardından:

```bash
talend-api-starter cloud workspaces
```

Bu proje Talend hesabı, lisans/trial, rol veya endpoint yetkisi sağlamaz. Canlı komutlar yalnız allowlist'teki GET isteklerini yerel makineden yapar.

## Kesin sınırlar

- Task başlatma/durdurma, publish, update, delete veya upload yoktur.
- Business row data, ham log, ham XML ve context/connection değeri dışa aktarılmaz.
- Private GitHub repo desteği bu başlangıç paketinde yoktur.
- Public issue veya Discussion'a token, client dosyası, log, private repo URL'si, tenant/workspace/run ID'si ya da `.item` / `.properties` içeriği koyma.

Daha fazla bilgi: [yetenek matrisi](supported-capabilities.md), [güvenlik modeli](security-model.md) ve [sorun giderme](troubleshooting.md).
