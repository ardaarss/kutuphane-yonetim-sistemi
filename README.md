# Kütüphane Yönetim Sistemi

Flask ve MSSQL kullanılarak geliştirilmiş web tabanlı bir kütüphane yönetim sistemidir.

## Özellikler

- Kullanıcı kayıt ve giriş sistemi
- Admin ve üye rolleri
- Kitap ekleme, listeleme, düzenleme ve silme
- Üye yönetimi
- Kitap ödünç alma ve iade işlemleri
- Rezervasyon sistemi
- Geciken kitap takibi
- İşlem geçmişi görüntüleme

## Kullanılan Teknolojiler

- Python
- Flask
- MSSQL
- pyodbc
- HTML
- CSS
- Bootstrap

## Kurulum

Projeyi klonlayın:

```bash
git clone https://github.com/ardaarss/kutuphane-yonetim-sistemi.git

## Veritabanı Kurulumu

Bu proje MSSQL kullanmaktadır.

1. SQL Server Management Studio uygulamasını açın.
2. `database.sql` dosyasını açın.
3. Dosyayı çalıştırarak `KutuphaneDB` veritabanını oluşturun.
4. `.env.example` dosyasını `.env` olarak kopyalayın.
5. `.env` içindeki veritabanı bilgilerini kendi SQL Server ayarlarınıza göre düzenleyin.

Varsayılan admin kullanıcı:

```text
E-posta: admin@kutuphane.com
Şifre: admin123