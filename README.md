# 🚀 Smart Lead Scraper & Data Extractor (Google Serper Engine)

Ek advanced, customizable web & local lead scraper jo **Google Maps Places API** aur **Serper Search API** ke zariye kisi bhi **Industry / Business Category** aur kisi bhi **City / Location** ka data automatically extract karta hai.

---

## 🎯 Ab Aap Kisi Bhi Tarah Ka Data Nikaal Sakte Hain!

Aap UI me directly select ya type kar sakte hain ki aapko kiska data chahiye:

### 1. Ready-made Popular Categories:
- 🏫 **Schools & Colleges** (CBSE, ICSE, Engineering, MBA, Universities)
- 🏥 **Hospitals & Healthcare** (Super Speciality, Multi Speciality, Eye, Maternity)
- 👨‍⚕️ **Doctors & Clinics** (Physicians, Dentists, Pediatricians, Dermatologists)
- 🏋️ **Gyms & Fitness Centers** (Crossfit, Unisex Gyms, Yoga, Zumba)
- 🍽️ **Restaurants, Cafes & Bakeries** (Fine Dining, Veg, Cafes, Bakeries)
- 🏨 **Hotels & Resorts** (Luxury, Budget, 3-Star, Guest Houses)
- 🏢 **Real Estate Agents & Builders** (Property Dealers, Brokers, Developers)
- 💻 **IT & Software Companies** (Web Dev, App Dev, Digital Marketing)
- ⚖️ **Lawyers & Law Firms** (Advocates, Corporate, Criminal, Civil)
- 💼 **Chartered Accountants (CA)** (Auditors, Tax Consultants, GST)
- 📚 **Coaching Institutes & Tuitions** (IIT-JEE, NEET, UPSC, SSC)
- 🚗 **Car Showrooms & Auto Services** (Dealers, Garages, Repair)
- 💄 **Beauty Parlours & Salons** (Makeup Studios, Hair Salons, Spas)
- 💊 **Pharmacies & Medical Stores** (Chemists, 24x7 Medical)
- ✍️ **Custom / Type Your Own** (Solar panel suppliers, Event managers, Interior designers, ya koi bhi business!)

### 2. Kisi Bhi City / Area Ka Selection:
- **City / Location**: e.g., `Delhi`, `Ghaziabad`, `Mumbai`, `Lucknow`, `Ayodhya`, `Noida`, `Bangalore`, etc.
- **Sub-Areas (Optional)**: e.g., `Indirapuram, Vaishali, Sector 62, Connaught Place`
- Button dabate hi **"⚡ Apply / Generate Queries"** automatic 20+ best Places & Search queries bana deta hai aur auto CSV file name set kar deta hai!

---

## 🌟 Key Features

1. **Modern Tkinter Graphical UI (`scraper_gui.py` & `app.py`)**:
   - **Live Data Table (Treeview)**: Real-time records stream hote hain bina screen hang huye.
   - **Google Ratings & Reviews Count**: Serper Places se business ki average rating aur total reviews count bhi extract hota hai!
   - **Live KPI Badges**: Total records, Phone count, Email count, aur Query progress.
   - **Live Progress Bar**: Visual progress indicator.
   - **Real-time Color-Coded Terminal**: Console logs in real time.
   - **Instant Search / Filter**: Live filter box to search by any keyword.
   - **Double-Click Row Details**: Popup window with 1-click copy buttons.

2. **Thread-Safe Architecture**:
   - GUI background daemon thread me chalti hai, isliye kabhi freeze ya "(Not Responding)" nahi hogi.

3. **Incremental Auto-Saving**:
   - Har record milte hi CSV me turant write aur flush hota hai — **Zero Data Loss Guarantee**.

4. **Pause / Resume & Stop**:
   - Scraping ko beech me Pause, Resume ya Stop kar sakte hain.

5. **Query Editor Tab**:
   - Aap chaho to auto-generated queries ko manually edit ya nayi queries add bhi kar sakte hain.

---

## ⚡ Kaise Chalayein (How to Run)

### Tarika 1: 1-Click Batch File (Sabse Aasan)
Project folder me `run_app.bat` par double-click karein.

### Tarika 2: GUI Mode (Python Command)
```bash
python app.py
```
*(Ya `python serper_ayodhya_scraper.py`)*

### Tarika 3: CLI / Terminal Mode
Aap CLI me bhi manchaha category aur location de sakte hain:
```bash
python serper_ayodhya_scraper.py --cli --category "Doctors & Clinics" --location "Delhi"
```
Ya default Ghaziabad Schools:
```bash
python serper_ayodhya_scraper.py --cli
```

---

## 📊 Extracted Columns in CSV
1. `Name`: Entity / Business / School / Hospital ka naam
2. `Category`: Specific category / type
3. `Phone Number`: Verified contact number
4. `Email`: Official website / contact page se extracted email
5. `Address`: Complete address
6. `Website`: Official website URL
7. `Rating`: Google Maps rating (e.g. 4.6)
8. `Reviews Count`: Total Google reviews count (e.g. 142)
