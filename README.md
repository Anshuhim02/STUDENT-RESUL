# Student Result Management System

A fully responsive, production‑ready web application built with **Flask**, **SQLite**, and **Bootstrap 5**.  
Teachers and administrators can securely manage student results – add, edit, view, delete, search, sort, export CSV, and upload result images.

---

## ✨ Features

- 🔐 **Authentication** – Register, login, logout (session based, password hashing)
- 📊 **Dashboard** – Statistics (total results, average %, highest %), quick action buttons
- ➕ **Add Result** – Dynamic subject rows, image upload, auto calculation (percentage & grade)
- ✏️ **Edit / Delete Result** – Full edit support, delete with image removal
- 👁️ **View Result** – Clean card with all details, subject table, image preview
- 📁 **CSV Export** – Export logged‑in user's results as `.csv`
- 🔎 **Search & Sort** – Search by student name, sort by percentage (highest/lowest)
- 📱 **100% Responsive** – Mobile‑first, fluid grid, touch‑friendly buttons
- 🖼️ **Image Upload** – jpg/png, secure filename, stored in `/static/uploads`
- 👤 **Profile Page** – View & update name, email, password, total result count

---

## ⚙️ Technology Stack

- **Backend**: Python 3, Flask, Werkzeug (password hashing)
- **Database**: SQLite (auto‑initialized)
- **Frontend**: HTML5, CSS3, Bootstrap 5, vanilla JavaScript, Font Awesome 6
- **Other**: CSV export, secure file upload, session control

---

## 🚀 Installation & Setup

1. **Clone or create the project folder**  
   ```bash
   mkdir student-result-app
   cd student-result-app