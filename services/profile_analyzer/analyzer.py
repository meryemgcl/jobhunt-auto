"""
services/profile_analyzer/analyzer.py
======================================
Aday profilini yukler.

Oncelik sirasi:
1. profile.yaml (proje koku) -- tercih edilen yontem
2. Geriye donuk uyumluluk icin get_mock_profile() -- sadece YAML yoksa

Bu sekilde profili degistirmek icin hic Python dosyasina dokunmaya gerek kalmaz.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROFILE_YAML_PATH = Path(__file__).resolve().parent.parent.parent / "profile.yaml"


def _load_yaml_profile(path: Path) -> dict | None:
    """profile.yaml'i standart kutuphanelerle yukle (PyYAML zorunlulugu yok)."""
    try:
        import yaml  # type: ignore[import]
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, dict):
            logger.debug("Profil YAML dosyasindan yuklendi: %s", path)
            return data
    except ImportError:
        # PyYAML yuklu degil -- basit satir parser'a dus
        return _parse_yaml_simple(path)
    except Exception as exc:
        logger.warning("profile.yaml okunamadi, mock profile kullaniliyor. hata=%s", exc)
    return None


def _parse_yaml_simple(path: Path) -> dict | None:
    """
    PyYAML olmadan temel YAML list alanlarini okur.
    Yalnizca profile.yaml'in beklenen yapisini destekler.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    profile: dict = {}
    current_key: str | None = None
    current_list: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()
        # Yorum ve bos satirlar
        if not line or line.lstrip().startswith("#"):
            continue
        # Liste elemani
        if line.lstrip().startswith("-") and current_key:
            value = line.lstrip().lstrip("-").strip().strip('"')
            current_list.append(value)
            continue
        # Anahtar: deger cifti
        if ":" in line and not line.startswith(" "):
            # Onceki listeyi kaydet
            if current_key and current_list:
                profile[current_key] = current_list
                current_list = []
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"')
            if value:
                profile[key] = value
                current_key = None
            else:
                current_key = key

    # Son liste
    if current_key and current_list:
        profile[current_key] = current_list

    return profile if profile else None


def get_profile() -> dict:
    """
    Aktif aday profilini don.
    profile.yaml mevcutsa oradan yukler; degilse mock profile'a dus.
    """
    if _PROFILE_YAML_PATH.exists():
        loaded = _load_yaml_profile(_PROFILE_YAML_PATH)
        if loaded:
            return loaded
    logger.warning(
        "profile.yaml bulunamadi (%s). Mock profil kullaniliyor. "
        "Lutfen profile.yaml olusturun.",
        _PROFILE_YAML_PATH,
    )
    return get_mock_profile()


def get_mock_profile() -> dict:
    """
    Geriye donuk uyumluluk icin saklanan mock profil.
    Yeni gelistirmelerde get_profile() kullanin.
    """
    return {
        "name": "Meryem Güçlü",
        "title": "Yazılım Geliştirici & Bilişim Sistemleri Öğrencisi",
        "core_skills": [
            "Python", "C#", "JavaScript", "SQL", "Google Gemini API",
            "Pandas", "Machine Learning", "CNN", "Unity", "Serverless",
        ],
        "experience_level": "Junior/Intern",
        "job_roles": [
            "AI Engineer Intern", "Data Analyst", "Junior Backend Developer",
            "Frontend Developer", "AR Developer",
        ],
        "preferred_locations": ["Sivas", "Erzurum", "Kayseri", "Remote", "Uzaktan", "Türkiye Geneli"],
        "target_skills_label": "Bilişim Sistemleri, Python, AI/ML, Backend, C#, SQL, Veri Analizi",
        "github_url": "https://github.com/meryemgcl",
        "linkedin_url": "https://www.linkedin.com/in/meryemgüçlü/",
    }


def extract_profile_with_gemini(cv_text: str) -> dict:
    """
    Kullanicinin CV metnini alir ve yapılandırılmıs bir profil dondurmek uzere
    tasarlanmis API entegrasyon noktasi.
    Simdilik get_profile()'a delege ediyor.
    """
    return get_profile()


if __name__ == "__main__":
    profile = get_profile()
    print(json.dumps(profile, indent=2, ensure_ascii=False))
