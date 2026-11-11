# Уулын цулын механик — RMR89 & Barton Q Dashboard

Python + Streamlit ашиглан чулуулгийн цулын чанарын **RMR (Bieniawski, 1989)** болон **Barton Q-system** үнэлгээ гаргах сургалтын dashboard.

## 1. Суулгах (Windows / Mac)

Python 3.10+ суусан байх шаардлагатай. Энэ хавтсыг VS Code дээр нээнэ. Терминалд:

```bash
python -m pip install -r requirements.txt
```

Дараа нь:

```bash
python -m streamlit run app.py
```

Windows дээр `python` танигдахгүй бол `py -m pip install -r requirements.txt` болон `py -m streamlit run app.py` гэж оролдоно.

Автоматаар browser-д `http://localhost:8501` хуудас нээгдэнэ. Windows-д `start_windows.bat` файл дээр хоёр дараад ажиллуулж болно (Python суусан байх шаардлагатай).

## 2. Dashboard-ийн боломж

- **Нийтлэг талбар:** UCS (MPa), RQD (%), ан цавын зай (м).
- **RMR89:** таван үндсэн бүлгийн оноо + чиглэлийн засвар; I–V ангилал.
- **Barton Q:** Q = (RQD/Jn) × (Jr/Ja) × (Jw/SRF); чулуулгийн чанарын ангилал.
- **График:** RMR хэмжүүр, Q логарифм хуваарь, RMR онооны бүрдэл.
- **Бүртгэл:** цэг тус бүрийг нэмэх, үр дүнг харьцуулах, CSV тайлан татах.

**Анхааруулга:** Эхний оруулсан утгууд нь зохиомол *жишээ*, Баянхөндийн уурхай болон бусад бодит талбайн баталгаат өгөгдөл **биш**. Бодит үнэлгээнд керний бүртгэл, геотехникийн зураглал, чулуулгийн туршилт хэрэгтэй.

## 3. Жишээ тооцоо (зөвхөн сургалтын)

Эхний утгууд: UCS=75 MPa, RQD=70%, ан цавын зай=0.4 м, persistence=2, aperture=5, roughness=3, infill=6, weathering=3, groundwater=10, tunnel orientation penalty=-5.

```text
RMR = 7 + 13 + 10 + (2+5+3+6+3) + 10 - 5 = 54
RMR class = III / Дунд

Q = (70/6) × (2/2) × (0.66/2.5) = 3.08
Q class = Муу
```

## 4. Файлууд

- `app.py`: Streamlit интерфейс, график, тайлан
- `rock_models.py`: ангилал, үнэлгээний цэвэр Python функцууд
- `test_rock_models.py`: томьёо ба үнэлгээний шалгалтын тест
- `requirements.txt`: Python сангууд

## 5. Багшид тайлбарлах богино дараалал

1. RMR ба Q үнэлгээний шаардлагатай хэмжилтийн утгуудыг сонгон оруулсан.
2. `rock_models.py` дотор RMR89-ийн таван бүлгийн оноог тусад нь гаргаад, чиглэлийн засварыг нэмсэн.
3. Q-ийн зургаан параметрийг хэрэглэж томьёогоор бодсон; RQD 10%-иас доош бол Q-д 10% авсан.
4. `app.py` нь гаралтыг ангилал, график, хүснэгт, CSV хэлбэрээр харуулдаг.
5. Үнэлгээ нь анхан шатны ангилал тул бэхэлгээний эцсийн шийдэл эсвэл FoS-ийн тооцоо биш.

## 6. Суурь эх сурвалж

- Bieniawski, Z. T. (1989). *Engineering Rock Mass Classifications*. Wiley.
- Barton, N., Lien, R., & Lunde, J. (1974). *Engineering classification of rock masses for the design of tunnel support*. Rock Mechanics, 6, 189–236.
- NGI: [Tunnels and the Q-system](https://www.ngi.no/en/research-and-consulting/infrastructure-container/tunnels-and-the-q-system/)
- [RMR89 үнэлгээний дэлгэрэнгүй хүснэгт](https://docs.geoassistant.org/core_elements/geo_parameters/classification_systems/rmrb)
- [Q-system тайлбар](https://docs.geoassistant.org/core_elements/geo_parameters/classification_systems/qbarton)

### Хэрэглэхдээ анхаарах нь
- Q-ийн Jn/Jr/Ja/Jw/SRF нь зөвхөн дурын утга биш, **тухайн талбайн нөхцөлд тохирсон** хүснэгтийн сонголт.
- RMR ан цавын чиглэлийн ангиллыг геологийн хэмжилтэд үндэслэн сонгоно.
- RMR/Q-ийн үнэлгээ өөр өөр зориулалттай, утгуудыг өөр хооронд нь тоогоор шууд харьцуулахгүй.
- Өндөр эрсдэлтэй инженерийн шийдвэрт энэ сургалтын dashboard-ийг дангаар ашиглахгүй.
