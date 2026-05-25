-- Kütüphane Yönetim Sistemi - MSSQL Veritabanı Kurulum Dosyası
-- Bu dosyayı SQL Server Management Studio (SSMS) üzerinde çalıştırabilirsiniz.
-- Varsayılan admin girişi:
-- E-posta: admin@kutuphane.com
-- Şifre: admin123
-- GitHub'a yükledikten sonra gerçek kullanımda bu şifreyi değiştirmeniz önerilir.

IF DB_ID('KutuphaneDB') IS NULL
BEGIN
    CREATE DATABASE KutuphaneDB;
END
GO

USE KutuphaneDB;
GO

-- Önce ilişkili tabloları sil
IF OBJECT_ID('dbo.Rezervasyonlar', 'U') IS NOT NULL DROP TABLE dbo.Rezervasyonlar;
IF OBJECT_ID('dbo.Odunc', 'U') IS NOT NULL DROP TABLE dbo.Odunc;
IF OBJECT_ID('dbo.Kitaplar', 'U') IS NOT NULL DROP TABLE dbo.Kitaplar;
IF OBJECT_ID('dbo.Kategoriler', 'U') IS NOT NULL DROP TABLE dbo.Kategoriler;
IF OBJECT_ID('dbo.Uyeler', 'U') IS NOT NULL DROP TABLE dbo.Uyeler;
GO

CREATE TABLE Uyeler (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ad_soyad NVARCHAR(100) NOT NULL,
    telefon NVARCHAR(20) NULL,
    eposta NVARCHAR(150) NOT NULL UNIQUE,
    sifre NVARCHAR(255) NOT NULL,
    rol NVARCHAR(20) NOT NULL DEFAULT 'uye',
    kayit_tarihi DATETIME NOT NULL DEFAULT GETDATE()
);
GO

CREATE TABLE Kategoriler (
    id INT IDENTITY(1,1) PRIMARY KEY,
    ad NVARCHAR(100) NOT NULL UNIQUE
);
GO

CREATE TABLE Kitaplar (
    id INT IDENTITY(1,1) PRIMARY KEY,
    baslik NVARCHAR(200) NOT NULL,
    yazar NVARCHAR(150) NOT NULL,
    tur NVARCHAR(100) NULL,
    stok INT NOT NULL DEFAULT 0,
    sayfa_sayisi INT NULL,
    yayinevi NVARCHAR(150) NULL,
    basim_yili INT NULL
);
GO

CREATE TABLE Odunc (
    id INT IDENTITY(1,1) PRIMARY KEY,
    uye_id INT NOT NULL,
    kitap_id INT NOT NULL,
    alis_tarihi DATETIME NOT NULL DEFAULT GETDATE(),
    iade_tarihi DATETIME NULL,
    durum NVARCHAR(30) NOT NULL DEFAULT 'Aktif',

    CONSTRAINT FK_Odunc_Uyeler 
        FOREIGN KEY (uye_id) REFERENCES Uyeler(id),

    CONSTRAINT FK_Odunc_Kitaplar 
        FOREIGN KEY (kitap_id) REFERENCES Kitaplar(id)
);
GO

CREATE TABLE Rezervasyonlar (
    id INT IDENTITY(1,1) PRIMARY KEY,
    uye_id INT NOT NULL,
    kitap_id INT NOT NULL,
    talep_tarihi DATETIME NOT NULL DEFAULT GETDATE(),
    durum NVARCHAR(30) NOT NULL DEFAULT 'Beklemede',

    CONSTRAINT FK_Rezervasyonlar_Uyeler 
        FOREIGN KEY (uye_id) REFERENCES Uyeler(id),

    CONSTRAINT FK_Rezervasyonlar_Kitaplar 
        FOREIGN KEY (kitap_id) REFERENCES Kitaplar(id)
);
GO

-- Başlangıç kategorileri
INSERT INTO Kategoriler (ad) VALUES
('Roman'),
('Bilim'),
('Tarih'),
('Yazılım'),
('Kişisel Gelişim'),
('Felsefe');
GO

-- Örnek kitaplar
INSERT INTO Kitaplar (baslik, yazar, tur, stok, sayfa_sayisi, yayinevi, basim_yili) VALUES
('Python Programlama', 'Örnek Yazar', 'Yazılım', 5, 320, 'Teknoloji Yayınları', 2024),
('Veri Bilimine Giriş', 'Örnek Yazar', 'Bilim', 3, 280, 'Akademi Yayınları', 2023),
('Kütüphane Yönetimi', 'Örnek Yazar', 'Kişisel Gelişim', 2, 180, 'Eğitim Yayınları', 2022);
GO

-- Varsayılan admin kullanıcı
INSERT INTO Uyeler (ad_soyad, telefon, eposta, sifre, rol) VALUES
('Admin Kullanıcı', '0000000000', 'admin@kutuphane.com', 'BURAYA_PYTHON_ILE_URETILEN_HASH_GELECEK', 'admin');
GO
