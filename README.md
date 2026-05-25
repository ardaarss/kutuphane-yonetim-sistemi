# Kütüphane Yönetim Sistemi

Flask ve MSSQL kullanılarak geliştirilmiş web tabanlı bir kütüphane yönetim sistemidir. Projede admin ve üye rolleri bulunmaktadır. Admin kullanıcılar kitap, üye, kategori, ödünç verme ve rezervasyon işlemlerini yönetebilir. Üye kullanıcılar ise kitapları görüntüleyebilir, rezervasyon talebi oluşturabilir ve kendi ödünç geçmişini takip edebilir.

## İçindekiler

- [Proje Hakkında](#proje-hakkında)
- [Özellikler](#özellikler)
- [Kullanılan Teknolojiler](#kullanılan-teknolojiler)
- [Proje Yapısı](#proje-yapısı)
- [Kurulum](#kurulum)
- [Veritabanı Kurulumu](#veritabanı-kurulumu)
- [Ortam Değişkenleri](#ortam-değişkenleri)
- [Uygulamayı Çalıştırma](#uygulamayı-çalıştırma)
- [Varsayılan Admin Bilgileri](#varsayılan-admin-bilgileri)
- [Geliştirilebilir Yönler](#geliştirilebilir-yönler)
- [Geliştirici](#geliştirici)

## Proje Hakkında

Bu proje, temel bir kütüphane yönetim sürecini dijital ortama taşımak amacıyla geliştirilmiştir. Sistem üzerinden kitaplar listelenebilir, yeni kitap eklenebilir, üyeler yönetilebilir, kitap ödünç verme ve iade işlemleri takip edilebilir.

Proje özellikle Flask ile backend geliştirme, MSSQL veritabanı bağlantısı, kullanıcı oturumu yönetimi, rol bazlı yetkilendirme ve temel web uygulaması geliştirme konularında pratik yapmak amacıyla hazırlanmıştır.

## Özellikler

- Kullanıcı kayıt ve giriş sistemi
- Şifrelerin hash'li olarak saklanması
- Admin ve üye rol yönetimi
- Kitap ekleme, listeleme, düzenleme ve silme
- Kitap arama
- Kategori yönetimi
- Üye listeleme ve üye detay sayfası
- Kitap ödünç verme işlemi
- Kitap iade alma işlemi
- Geciken kitap takibi
- Rezervasyon talebi oluşturma
- Rezervasyon onaylama ve reddetme
- İşlem geçmişi görüntüleme
- `.env` dosyası ile güvenli yapılandırma

## Kullanılan Teknolojiler

- Python
- Flask
- MSSQL
- pyodbc
- python-dotenv
- Werkzeug
- HTML
- CSS
- Bootstrap

## Proje Yapısı

```text
kutuphane-yonetim-sistemi/
│
├── app.py
├── database.sql
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
└── templates/
    ├── giris.html
    ├── kayit.html
    ├── index.html
    ├── kitaplar.html
    ├── kitap_duzenle.html
    ├── uyeler.html
    ├── uye_detay.html
    ├── odunc.html
    ├── rezervasyonlar.html
    ├── kategoriler.html
    └── gecmis.html
```

## Kurulum

Öncelikle projeyi bilgisayarınıza klonlayın:

```bash
git clone https://github.com/ardaars/kutuphane-yonetim-sistemi.git
```

Proje klasörüne girin:

```bash
cd kutuphane-yonetim-sistemi
```

Gerekli Python paketlerini yükleyin:

```bash
pip install -r requirements.txt
```

## Veritabanı Kurulumu

Bu proje MSSQL kullanmaktadır. Veritabanı kurulumu için `database.sql` dosyası hazırlanmıştır.

SQL Server Management Studio üzerinden:

1. SQL Server Management Studio uygulamasını açın.
2. `database.sql` dosyasını açın.
3. Üst menüden **Execute** butonuna basın.
4. `KutuphaneDB` veritabanı ve gerekli tablolar otomatik olarak oluşturulur.

Oluşturulan temel tablolar:

- `Uyeler`
- `Kitaplar`
- `Kategoriler`
- `Odunc`
- `Rezervasyonlar`

## Ortam Değişkenleri

Projede gizli bilgiler doğrudan kod içinde tutulmaz. Bunun yerine `.env` dosyası kullanılır.

Öncelikle `.env.example` dosyasını kopyalayıp `.env` adında yeni bir dosya oluşturun.

Örnek `.env` içeriği:

```env
SECRET_KEY=change-this-secret-key

DB_DRIVER=ODBC Driver 17 for SQL Server
DB_SERVER=localhost\SQLEXPRESS
DB_NAME=KutuphaneDB
DB_TRUSTED_CONNECTION=yes
DB_TRUST_SERVER_CERTIFICATE=yes
```

Kendi bilgisayarınızdaki SQL Server adına göre `DB_SERVER` değerini düzenleyin.

Örneğin:

```env
DB_SERVER=LAPTOP-XXXXXXX\SQLEXPRESS
```

> Not: `.env` dosyası `.gitignore` içinde yer aldığı için GitHub'a yüklenmez.

## Uygulamayı Çalıştırma

Kurulum ve veritabanı ayarları tamamlandıktan sonra uygulamayı başlatmak için:

```bash
python app.py
```

Uygulama varsayılan olarak şu adreste çalışır:

```text
http://127.0.0.1:5000
```

## Varsayılan Admin Bilgileri

`database.sql` dosyası çalıştırıldığında varsayılan bir admin kullanıcı oluşturulur.

```text
E-posta: admin@kutuphane.com
Şifre: admin123
```

Güvenlik açısından gerçek kullanımda bu şifrenin değiştirilmesi önerilir.

## Rol Yetkileri

### Admin

Admin kullanıcılar şu işlemleri yapabilir:

- Kitap ekleme, düzenleme ve silme
- Üye ekleme ve silme
- Kategori yönetimi
- Kitap ödünç verme
- Kitap iade alma
- Rezervasyonları onaylama veya reddetme
- İşlem geçmişini görüntüleme

### Üye

Üye kullanıcılar şu işlemleri yapabilir:

- Kitapları görüntüleme
- Kitap arama
- Rezervasyon talebi oluşturma
- Kendi ödünç kitaplarını ve geçmişini görüntüleme

## Güvenlik Notları

- Kullanıcı şifreleri düz metin olarak saklanmaz.
- Şifreler `Werkzeug` ile hash'lenerek veritabanına kaydedilir.
- Gizli anahtar ve veritabanı bilgileri `.env` dosyasında tutulur.
- Admin işlemleri rol kontrolü ile sınırlandırılmıştır.

## Geliştirilebilir Yönler

Projeye ileride şu özellikler eklenebilir:

- Şifre değiştirme sayfası
- Profil güncelleme ekranı
- Kitap kapak görseli ekleme
- Daha detaylı arama ve filtreleme
- Admin panelinde istatistik grafikleri
- E-posta bildirim sistemi
- Unit test yapısı
- Docker desteği
- API endpoint'leri

## Geliştirici

**Arda Arslan**

GitHub: [ardaars](https://github.com/ardaars)
