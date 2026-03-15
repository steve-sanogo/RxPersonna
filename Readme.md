# 🌌 Extraction de Réseaux de Personnages - Cycle de Fondation

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![NLP](https://img.shields.io/badge/NLP-SpaCy%20%7C%20Flair-green)
![Score](https://img.shields.io/badge/F1--Score-0.54-orange)
![Status](https://img.shields.io/badge/Status-Completed-success)

> **Projet AMS - Analyse et Modélisation de Systèmes** > Transformation de textes bruts (*Isaac Asimov*) en graphes sociaux structurés via une pipeline TALN hybride.

---

## 📋 Présentation

Ce projet vise à extraire automatiquement les réseaux d'interactions entre personnages à partir du corpus complexe de science-fiction *Le Cycle de Fondation* d'Isaac Asimov. 

Le pipeline développé combine plusieurs techniques de TALN pour surmonter les défis spécifiques au corpus : néologismes (*Trantor, Mycogène*), homonymies complexes (*Famille Seldon*) et titres multiples (*L'Empereur, R. Daneel*).

### 🏆 Résultats Clés
* **F1-Score Global : 0.54** (Top performance sur le leaderboard).
* **Approche :** Hybride (Règles + Deep Learning).
* **Sortie :** Fichiers GraphML (compatibles Gephi) et visualisations PNG.

---

## ⚙️ Architecture du Pipeline

Le projet repose sur une architecture modulaire et orientée objet (POO) pour garantir robustesse et reproductibilité.
![Pipeline](data/images/pipeline.jpg)