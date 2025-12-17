# Voice In

**Votre voix, partout.**

Voice In est un outil de dictée vocale de nouvelle génération, alimenté par l'IA, qui fonctionne dans n'importe quelle application sur votre PC.
Il suffit de maintenir la touche enfoncée et de parler. L'IA avancée comprend votre contexte, ajoute la ponctuation, corrige la grammaire et saisit un texte parfait instantanément.

[日本語](../README.md) | [English](README_en.md) | [한국어](README_ko.md) | [中文](README_zh.md)

---

## ✨ Pourquoi Voice In ?

- **Tapez partout** : Bloc-notes, Navigateur, Slack, Éditeurs de code... fonctionne dans n'importe quelle fenêtre active.
- **Plus que de la dictée** : Supprime les hésitations (comme "euh"), formate automatiquement le texte et adapte le ton.
- **Choix de l'IA** : IA cloud ultra-rapide (Groq, Google Gemini) ou traitement local respectueux de la vie privée (Local Whisper).
- **Multiplateforme** : Principalement pour Linux, avec un support expérimental pour Windows et macOS.

## 🚀 Commencer

### 1. Télécharger
Téléchargez la dernière version pour votre système d'exploitation depuis la page [Releases](https://github.com/watawatan1984/voice-inn-linux/releases).

### 2. Installer et exécuter
Lancez le fichier téléchargé.

> **Note** : Sur Linux, assurez-vous que le fichier dispose des permissions d'exécution.

### 3. Assistant de configuration
L'assistant vous guidera lors du premier lancement :
1. **Choisir le fournisseur d'IA** : Choisissez `Groq` (rapide), `Gemini` (précis) ou `Local` (hors ligne).
2. **Clé API** : Entrez votre clé API gratuite si vous utilisez des fournisseurs cloud.
3. **Microphone** : Sélectionnez et testez votre périphérique d'entrée.

## 🎙️ Comment utiliser

C'est extrêmement simple.

1. Cliquez sur le champ de texte où vous souhaitez écrire.
2. **Maintenez la touche `Left Alt` enfoncée** (ou votre raccourci configuré).
3. Parlez dans votre microphone. Une icône de microphone apparaîtra.
4. Relâchez la touche lorsque vous avez terminé.
5. L'IA traite votre parole et tape le texte automatiquement ✨

---

## ⚙️ Personnalisation

Faites un clic droit sur l'icône dans la barre d'état système et sélectionnez `Settings` pour plus d'options :

**Language (Langue)** : Changer la langue de l'interface.

### 1. General (Général)
Configuration de base.
- **AI Provider** : `Groq` (Ultra-rapide), `Gemini` (Haute précision), `Local` (Confidentialité/Hors ligne).
- **Gemini Model / Groq API Key** : Clé API/Modèle.
- **Input Device** : Microphone.
- **Input Gain** : Gain d'entrée (dB).
- **Hold Key** : Touche d'enregistrement (Défaut : `Left Alt`).
- **Max Recording** : Durée max d'enregistrement.
- **Min Valid Duration** : Durée min valide.
- **Auto Paste** : Collage automatique (ON/OFF).
- **Paste Delay** : Délai de collage (ms).

### 2. Prompts
Personnaliser les instructions IA.
- **Groq Whisper Prompt** : Indices de contexte (ex: "Termes médicaux").
- **Refine System Prompt** : Règles de formatage (ex: "Traduire en anglais").

### 3. Dictionary (Dictionnaire)
- **From** : Mot incorrect.
- **To** : Mot correct.

### 4. Local Whisper
- **Model Size** : Taille du modèle (`large-v3`, etc.).
- **Device** : `cuda` (GPU) ou `cpu`.
- **Compute Type** : Précision (`float16`, `int8`).

---

## 🛠️ Pour les développeurs

Pour les détails techniques et les instructions de compilation, veuillez consulter [DEVELOPMENT.md](DEVELOPMENT.md).

Voice In est construit avec Rust (noyau audio) et Python (intégration UI/IA) et est open source.

---
**License**: MIT
