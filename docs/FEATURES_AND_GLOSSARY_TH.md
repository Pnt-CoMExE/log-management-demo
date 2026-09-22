# คู่มือฟังก์ชันทั้งหมด + อภิธานศัพท์

เอกสารนี้อธิบายว่าแต่ละส่วนของระบบทำอะไร และอธิบายศัพท์เทคนิคที่ใช้ในโปรเจค/โจทย์

---

## ส่วนที่ 1: ภาพรวมระบบทำงานอย่างไร

```text
แหล่ง log หลายแบบ
   │
   ▼
[ Ingest ] ──รับเข้า──► [ Normalize ] ──แปลง schema──► [ PostgreSQL ]
                                                          │
                    ┌─────────────────────────────────────┤
                    ▼                                     ▼
              [ Search / Dashboard ]                 [ Alert Engine ]
                    │                                     │
                    ▼                                     ▼
              [ Web UI (React) ]  ◄── Auth (JWT + RBAC + Tenant)
```

คิดง่ายๆ ว่าเป็น **โรงงานรับพัสดุหลายยี่ห้อ** → ติดป้ายมาตรฐานเดียวกัน → เก็บคลัง → ค้นหา/สรุป → เตือนเมื่อผิดปกติ

---

## ส่วนที่ 2: ฟังก์ชันฝั่งเว็บ (UI)

เว็บคือ **Operations Console** มี 4 แท็บหลักหลังล็อกอิน

### 2.1 Login / Logout

| สิ่งที่ทำ | รายละเอียด |
|----------|------------|
| เข้าสู่ระบบ | ส่ง username/password ไป API → ได้ **JWT token** เก็บในเบราว์เซอร์ |
| แสดงบทบาท | โชว์ว่าเป็น `admin` หรือ `viewer` และ tenant ของผู้ใช้ |
| ออกจากระบบ | ลบ token ออกจากเครื่อง แล้วกลับหน้า login |

**บัญชีเดโม**

| User | Role | Tenant | สิทธิ์ |
|------|------|--------|--------|
| `admin` | Admin | demoA | ดูทุก tenant, ingest ได้, จัดการ alert rule |
| `viewer` | Viewer | demoA | ดูได้อย่างเดียว เฉพาะ demoA |
| `viewer_b` | Viewer | demoB | ดูได้อย่างเดียว เฉพาะ demoB |

---

### 2.2 Dashboard (แผงสรุป)

แสดงภาพรวมเหตุการณ์ (ค่าเริ่มต้นประมาณ 24 ชั่วโมงล่าสุด)

| ส่วนบน UI | ความหมาย |
|-----------|----------|
| **Events (range)** | จำนวน event ทั้งหมดในช่วงที่สรุป |
| **Open alerts** | จำนวนการแจ้งเตือนที่ยังสถานะ `open` |
| **Sources** | จำนวนชนิดแหล่งที่มาที่มีในข้อมูล |
| **Timeline** | กราฟจำนวน event ตามเวลา (รายชั่วโมง) |
| **Top IP** | IP ต้นทางที่ปรากฏบ่อยสุด |
| **Top User** | ชื่อผู้ใช้ที่เกี่ยวกับ event บ่อยสุด |
| **Top Event Type** | ประเภทเหตุการณ์ที่พบบ่อย |
| **By source** | แท่งกราฟแยกตามแหล่ง (firewall, aws, ad, …) |

**ตัวกรอง (Filter)**

- **Tenant** — เลือกองค์กร/ลูกค้าจำลอง (`demoA`, `demoB`, หรือทั้งหมดสำหรับ Admin)
- **Source** — กรองตามแหล่ง log
- **Search** — ค้นข้อความใน user / IP / event type / host ฯลฯ

ข้อมูลรีเฟรชอัตโนมัติประมาณทุก 15 วินาที หรือกด **Refresh**

---

### 2.3 Events (รายการเหตุการณ์)

ตาราง event ทีละรายการ หลัง normalize แล้ว

คอลัมน์สำคัญ:

| คอลัมน์ | ความหมาย |
|---------|----------|
| Time | เวลาเกิดเหตุ (`@timestamp`) |
| Tenant | เจ้าของข้อมูล |
| Source | แหล่งที่มา (firewall, api, aws, …) |
| Type | ประเภทเหตุการณ์ เช่น `LogonFailed`, `CreateUser` |
| User | ผู้ใช้ที่เกี่ยวข้อง |
| Src IP | IP ต้นทาง |
| Action | การกระทำ เช่น `deny`, `login`, `quarantine` |

ใช้คู่กับ filter ด้านบนเพื่อไล่ล่าเหตุการณ์เฉพาะเจาะจง

---

### 2.4 Alerts (การแจ้งเตือน)

แสดงผลลัพธ์จาก **กฎตรวจจับ (Alert Rule)**

ในเดโมมีกฎหลัก:

> **Failed Login Burst**  
> ถ้า IP เดิมมีเหตุการณ์ล็อกอินล้มเหลว ≥ 3 ครั้ง ภายใน 5 นาที → สร้าง Alert

แต่ละ alert มี: ชื่อกฎ, tenant, ข้อความ, IP, จำนวน event, สถานะ (`open` / `acked`)

---

### 2.5 Ingest (นำข้อมูลเข้า) — เฉพาะ Admin

| วิธี | ทำอะไร |
|------|--------|
| **ส่ง JSON** | ยิง `POST /api/ingest` จากกล่องข้อความบนเว็บ |
| **อัปโหลดไฟล์** | ส่งไฟล์ `.json` / `.ndjson` / `.log` เข้า `POST /api/ingest/file` พร้อมระบุ tenant และ source hint |

Viewer เปิดแท็บนี้แล้วจะถูกบอกว่าอ่านอย่างเดียว (ไม่มีสิทธิ์เขียน)

---

## ส่วนที่ 3: ฟังก์ชันฝั่ง Backend (API)

Base path ส่วนใหญ่ขึ้นต้นด้วย `/api`

### 3.1 Authentication

| Endpoint | หน้าที่ |
|----------|---------|
| `POST /api/auth/login` | ตรวจรหัสผ่าน → ออก JWT ที่มี `role` + `tenant` |

รหัสผ่านเก็บแบบ **hash ด้วย bcrypt** ไม่เก็บ plain text

---

### 3.2 Ingest (รับ log)

| Endpoint | หน้าที่ |
|----------|---------|
| `POST /api/ingest` | รับ JSON object หรือ array แล้ว normalize + บันทึก |
| `POST /api/ingest/syslog` | รับข้อความ syslog หนึ่งบรรทัด (หลัง UDP forwarder ส่งต่อ) |
| `POST /api/ingest/file` | รับไฟล์ batch แล้ว parse ตามนามสกุล |

หลังบันทึกจะ **evaluate กฎ alert** ด้วยทันที (นอกเหนือจาก job รอบละ 1 นาที)

Alias ตามโจทย์: `POST /ingest` ก็ชี้มาทางเดียวกันได้

---

### 3.3 Search & Dashboard

| Endpoint | หน้าที่ |
|----------|---------|
| `GET /api/events/search` | ค้นหา/กรอง event (tenant, source, event_type, src_ip, user, q, start, end, limit, offset) |
| `GET /api/dashboard/summary` | ส่งสถิติ Top-N + timeline + by_source |

Viewer ถูกบังคับ filter เป็น tenant ของตัวเองเสมอ แม้จะส่งพารามิเตอร์อื่นมาก็ตาม

---

### 3.4 Alerts

| Endpoint | หน้าที่ |
|----------|---------|
| `GET /api/alerts` | รายการ alert |
| `GET /api/alerts/rules` | รายการกฎ |
| `POST /api/alerts/rules` | สร้างกฎใหม่ (Admin) |
| `POST /api/alerts/evaluate` | รันตรวจจับทันที (Admin) |
| `PATCH /api/alerts/{id}/ack` | รับทราบ alert (เปลี่ยนเป็น `acked`) |

---

### 3.5 Health

| Endpoint | หน้าที่ |
|----------|---------|
| `GET /api/health` | เช็กว่าระบบยังตอบได้ (`status: ok`) |

---

## ส่วนที่ 4: Normalization (หัวใจของระบบ)

**Normalize** = แปลง log คนละรูปแบบ ให้เหลือฟิลด์มาตรฐานชุดเดียวกัน

ตัวอย่าง mapping:

| ของเดิม | เข้า schema กลาง |
|---------|------------------|
| `ip` หรือ `src` | `src_ip` |
| `@timestamp` | `timestamp` |
| `cloud.account_id` | `cloud_account_id` |
| Syslog `action=deny src=...` | `action`, `src_ip`, … |
| ทั้งก้อนเดิม | เก็บใน `raw` เพื่อย้อนดู |

ฟิลด์สำคัญใน schema กลาง:

`timestamp`, `tenant`, `source`, `vendor`, `product`, `event_type`, `severity`, `action`, `src_ip`, `dst_ip`, `user`, `host`, `process`, `cloud_*`, `raw`, `tags`

ทำไมต้องมี: ถ้าไม่ normalize Dashboard/Alert จะเขียน logic แยกตาม vendor ไม่รู้จบ

---

## ส่วนที่ 5: แหล่งข้อมูล (Sources) ที่รองรับ

| Source | วิธีเข้าสู่ระบบในเดโม |
|--------|------------------------|
| **firewall / network** | Syslog UDP (Appliance) หรืออัปโหลด `.log` |
| **api** | `POST /api/ingest` JSON |
| **crowdstrike** | sample JSON |
| **aws** | sample CloudTrail JSON |
| **m365** | sample Microsoft 365 Audit JSON |
| **ad** | sample Windows Security (เช่น Event 4625) |

โจทย์ไม่บังคับต่อระบบจริงทุกอัน — สำคัญคือมี ≥ 4 ทางที่ยิงเข้าได้จริง + normalize รวมศูนย์

---

## ส่วนที่ 6: ระบบพื้นหลัง (Background jobs)

| Job | ความถี่ | ทำอะไร |
|-----|--------|--------|
| Alert evaluate | ทุก 1 นาที (+ หลัง ingest) | ตรวจกฎ failed login burst |
| Retention purge | ทุก 6 ชั่วโมง | ลบ event ที่เก่ากว่า `RETENTION_DAYS` (ค่าเริ่มต้น 7 วัน) |

---

## ส่วนที่ 7: Deployment ที่เกี่ยวข้องกับฟังก์ชัน

| โหมด | ได้ฟังก์ชันอะไร |
|------|----------------|
| **Appliance** (`docker compose`) | UI + API + Postgres + **Syslog UDP** ครบ |
| **SaaS Render** | UI+API ใน container เดียว + Postgres บนคลาวด์ + **HTTPS** (ไม่มี Syslog สาธารณะ) |

---

## ส่วนที่ 8: อภิธานศัพท์ (Glossary)

เรียงตามที่พบบ่อยในโจทย์และโปรเจค

### A–D

| ศัพท์ | ความหมายง่ายๆ |
|-------|----------------|
| **Alert / Alerting** | การแจ้งเตือนเมื่อเข้าเงื่อนไขที่ตั้งไว้ |
| **API (Application Programming Interface)** | ช่องทางให้โปรแกรมคุยกัน (เช่น frontend เรียก backend) |
| **Appliance** | ติดตั้งรันบนเครื่อง/VM เครื่องเดียวแบบกล่องสำเร็จรูป |
| **AuthN (Authentication)** | พิสูจน์ว่า “คุณเป็นใคร” (ล็อกอิน) |
| **AuthZ (Authorization)** | ตัดสินว่า “คุณทำอะไรได้บ้าง” หลังล็อกอินแล้ว |
| **Backend** | ฝั่งเซิร์ฟเวอร์ ตรรกะธุรกิจ ฐานข้อมูล API |
| **Burst** | เหตุการณ์ถี่ผิดปกติในเวลาสั้นๆ (เช่น login fail รัวๆ) |
| **Dashboard** | หน้าสรุปด้วยกราฟ/ตัวเลข |
| **Docker / Docker Compose** | เครื่องมือแพ็กแอปเป็น container แล้วรันหลายบริการพร้อมกันด้วยไฟล์เดียว |
| **DX (Developer Experience)** | ความสะดวกของนักพัฒนา เช่น README, Makefile, `.env.example`, tests |

### E–L

| ศัพท์ | ความหมายง่ายๆ |
|-------|----------------|
| **Enrichment** | เติมข้อมูลระหว่าง ingest เช่น หาประเทศจาก IP (geoip) — ในเดโมนี้ยังเป็น nice-to-have |
| **Event / Log** | บันทึกเหตุการณ์หนึ่งครั้งจากระบบ |
| **Filter** | ตัวกรองข้อมูลตามเงื่อนไข |
| **Frontend / UI** | หน้าเว็บที่ผู้ใช้เห็นและคลิก |
| **Full-Stack** | ทำทั้ง frontend + backend (+ มักรวม deploy/data) |
| **GIN index** | ชนิด index ของ PostgreSQL เหมาะกับค้นใน JSON/array |
| **HTTPS / TLS** | การเข้ารหัสทราฟฟิกบนเว็บ กันแอบอ่านระหว่างทาง |
| **Ingest / Ingestion** | ขั้นตอน “รับข้อมูลเข้า” ระบบ |
| **JSONB** | ชนิดข้อมูล JSON ใน PostgreSQL ที่ค้นหาได้ดี |
| **JWT (JSON Web Token)** | โทเคนหลังล็อกอิน แนบไปกับคำขอเพื่อยืนยันตัวตน |

### M–R

| ศัพท์ | ความหมายง่ายๆ |
|-------|----------------|
| **Multi-tenant / Tenant** | แยกข้อมูลหลายลูกค้า/องค์กรในระบบเดียว — ที่นี่ใช้ค่า `demoA`, `demoB` |
| **Logical multi-tenant** | แยกด้วยเงื่อนไขในตารางร่วม (แถวคนละ tenant) ไม่ได้แยกฐานคนละตัว |
| **Normalize / Schema กลาง** | แปลงฟอร์แมตต่างๆ ให้เหลือโครงสร้างฟิลด์มาตรฐานชุดเดียว |
| **OpenAPI / Swagger** | เอกสาร API อัตโนมัติ (เปิดที่ `/docs` ของ FastAPI) |
| **Pipeline (Data pipeline)** | สายพานข้อมูล: รับ → แปลง → เก็บ → ใช้ |
| **PostgreSQL** | ฐานข้อมูลเชิงสัมพันธ์ ที่โปรเจคนี้ใช้เก็บ events |
| **Protocol** | กติกาการสื่อสาร เช่น HTTP, UDP Syslog |
| **RBAC (Role-Based Access Control)** | จำกัดสิทธิ์ตามบทบาท เช่น Admin / Viewer |
| **Retention** | นโยบายเก็บข้อมูลนานเท่าไร แล้วลบ/หมุนข้อมูลเก่า |
| **REST** | สไตล์ออกแบบ API บน HTTP (GET/POST/…) |
| **Reverse proxy** | ตัวกลางรับ HTTPS แล้วส่งต่อเข้าแอปภายใน |

### S–Z

| ศัพท์ | ความหมายง่ายๆ |
|-------|----------------|
| **SaaS (Software as a Service)** | ใช้ผ่านอินเทอร์เน็ต มี URL ไม่ต้องติดตั้งเองบนเครื่องกรรมการ |
| **Sample / Simulator** | ข้อมูลหรือสคริปต์จำลอง ใช้แทนการต่อระบบจริง |
| **Schema** | โครงฟิลด์ของข้อมูล |
| **SIEM** | ระบบใหญ่สำหรับรวม log + ตรวจจับภัย (ของจริง) — โปรเจคนี้เป็น **demo** ไม่ใช่ SIEM เต็มระบบ |
| **SOC** | ศูนย์ปฏิบัติการความปลอดภัย ที่นักวิเคราะห์เฝ้าดูเหตุการณ์ |
| **Source** | แหล่งกำเนิด log (firewall, aws, ad, …) |
| **Syslog** | มาตรฐานส่ง log โดยเฉพาะอุปกรณ์เครือข่าย มักใช้พอร์ต UDP 514 |
| **Timeline** | กราฟแนวเวลา แสดงปริมาณเหตุการณ์ตามช่วงเวลา |
| **Top-N** | อันดับสูงสุด N รายการ (เช่น Top 5 IP) |
| **UDP** | โปรโตคอลส่งข้อมูลแบบไม่ยืนยันรับ (เร็ว ใช้กับ syslog บ่อย) |
| **Webhook** | ให้ระบบยิง HTTP ไปแจ้งระบบอื่นเมื่อเกิดเหตุ — เดโมหลักแสดงใน UI |

### ศัพท์จากโจทย์ที่เจอบ่อย

| ศัพท์ใน assignment | ความหมาย |
|--------------------|----------|
| **Must-have** | ฟีเจอร์ที่ต้องมีถึงจะผ่านเกณฑ์ |
| **Nice-to-have** | มีแล้วได้คะแนนพิเศษ แต่ไม่บังคับ |
| **Acceptance Checklist** | รายการที่กรรมการจะเทสทีละข้อ |
| **Deliverables** | สิ่งที่ต้องส่ง (repo, docs, video, URL) |
| **Normalize รวมศูนย์** | ทุกแหล่งต้องเข้า schema เดียวก่อนเก็บ |
| **Strong Hire** | เกณฑ์คะแนนสูง (≥ 85) ที่บ่งชี้ว่าทำได้แข็งแรง |

---

## ส่วนที่ 9: สรุปสั้นมาก (จำไว้พูดเดโม)

1. **Ingest** — รับ log หลายทาง  
2. **Normalize** — จัดฟอร์แมตให้เหมือนกัน  
3. **Store/Search** — เก็บแล้วค้นได้  
4. **Dashboard** — สรุปภาพรวม  
5. **Alert** — เตือนเมื่อผิดปกติ  
6. **Auth + Tenant** — ล็อกอิน + จำกัดสิทธิ์/ข้อมูล  
7. **Deploy 2 โหมด** — เครื่องเดียว หรือคลาวด์ HTTPS  

อ่านคู่กับ: [PURPOSE.md](PURPOSE.md) · [TESTING.md](TESTING.md) · [DEMO_SCRIPT_TH.md](DEMO_SCRIPT_TH.md)
