SET FOREIGN_KEY_CHECKS = 0;
SET sql_mode = 'PIPES_AS_CONCAT';
-- ============================================================
--   FACULTY OF COMMERCE - EGYPTIAN UNIVERSITY DATABASE
--   Cairo University - Faculty of Commerce
--   Academic Year: 2024/2025
-- ============================================================

-- ─────────────────────────────────────────────
-- DROP TABLES (clean slate)
-- ─────────────────────────────────────────────
DROP TABLE IF EXISTS FacPayments;
DROP TABLE IF EXISTS FacUsers;
DROP TABLE IF EXISTS Grades;
DROP TABLE IF EXISTS Enrollments;
DROP TABLE IF EXISTS CoursePrerequisites;
DROP TABLE IF EXISTS Courses;
DROP TABLE IF EXISTS Students;
DROP TABLE IF EXISTS Instructors;
DROP TABLE IF EXISTS Departments;
DROP TABLE IF EXISTS AcademicYears;
DROP TABLE IF EXISTS Faculty;

-- ============================================================
-- 1. FACULTY
-- ============================================================
CREATE TABLE Faculty (
    faculty_id      INTEGER PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(255)    NOT NULL,
    established     INTEGER,
    dean            VARCHAR(255),
    location        VARCHAR(255),
    phone           VARCHAR(255),
    email           VARCHAR(255)
);

INSERT INTO Faculty VALUES
(1, 'Faculty of Commerce', 1932, 'Prof. Dr. Ahmed Mohamed El-Sayed',
 'Cairo University, Giza, Egypt', '+20-2-35676510', 'commerce@cu.edu.eg');


-- ============================================================
-- 2. DEPARTMENTS
-- ============================================================
CREATE TABLE Departments (
    dept_id         INTEGER PRIMARY KEY AUTO_INCREMENT,
    faculty_id      INTEGER NOT NULL REFERENCES Faculty(faculty_id),
    name            VARCHAR(255)    NOT NULL,
    head_of_dept    VARCHAR(255),
    established     INTEGER,
    description     VARCHAR(255)
);

INSERT INTO Departments (faculty_id, name, head_of_dept, established, description) VALUES
(1, 'Accounting',            'Prof. Dr. Hossam Abdel Aziz',    1935, 'Financial & managerial accounting, auditing'),
(1, 'Business Administration','Prof. Dr. Sahar Mahmoud Khalil', 1940, 'Management, HRM, strategic planning'),
(1, 'Economics',              'Prof. Dr. Khaled Ibrahim Nour',  1932, 'Macro/micro economics, econometrics'),
(1, 'Statistics & Mathematics','Prof. Dr. Mona Gamal Hassan',   1950, 'Applied statistics, operations research'),
(1, 'Marketing',              'Prof. Dr. Tarek Samir Fouad',    1975, 'Consumer behaviour, digital marketing'),
(1, 'Finance & Investment',   'Prof. Dr. Rania Adel Mansour',   1980, 'Corporate finance, capital markets, investment');


-- ============================================================
-- 3. ACADEMIC YEARS (study levels)
-- ============================================================
CREATE TABLE AcademicYears (
    year_level      INTEGER PRIMARY KEY,   -- 1,2,3,4
    label           VARCHAR(255) NOT NULL,
    total_credit_hrs INTEGER,
    min_pass_gpa    REAL
);

INSERT INTO AcademicYears VALUES
(1, 'First  Year  – Foundation',      30, 2.0),
(2, 'Second Year  – Intermediate',    32, 2.0),
(3, 'Third  Year  – Advanced',        34, 2.0),
(4, 'Fourth Year  – Specialisation',  36, 2.0);


-- ============================================================
-- 4. INSTRUCTORS
-- ============================================================
CREATE TABLE Instructors (
    instructor_id   INTEGER PRIMARY KEY AUTO_INCREMENT,
    dept_id         INTEGER NOT NULL REFERENCES Departments(dept_id),
    first_name      VARCHAR(255) NOT NULL,
    last_name       VARCHAR(255) NOT NULL,
    title           VARCHAR(255),          -- Prof. / Assoc. Prof. / Dr. / Lecturer
    specialisation  VARCHAR(255),
    email           VARCHAR(255),
    phone           VARCHAR(255),
    hire_date       VARCHAR(255),
    office_room     VARCHAR(255)
);

INSERT INTO Instructors (dept_id,first_name,last_name,title,specialisation,email,phone,hire_date,office_room) VALUES
-- Accounting (dept 1)
(1,'Ahmed',   'El-Sayed',   'Prof.',       'Financial Accounting',       'a.elsayed@cu.edu.eg',   '+20-111-0001','1995-09-01','A101'),
(1,'Fatma',   'Hassan',     'Assoc. Prof.','Auditing & Assurance',       'f.hassan@cu.edu.eg',    '+20-111-0002','2002-09-01','A102'),
(1,'Omar',    'Abdallah',   'Dr.',         'Cost Accounting',            'o.abdallah@cu.edu.eg',  '+20-111-0003','2010-09-01','A103'),
-- Business Admin (dept 2)
(2,'Sahar',   'Mahmoud',    'Prof.',       'Strategic Management',       's.mahmoud@cu.edu.eg',   '+20-111-0004','1998-09-01','B101'),
(2,'Youssef', 'Naguib',     'Dr.',         'Human Resource Management',  'y.naguib@cu.edu.eg',    '+20-111-0005','2008-09-01','B102'),
(2,'Nadia',   'Farouk',     'Lecturer',    'Organisational Behaviour',   'n.farouk@cu.edu.eg',    '+20-111-0006','2015-09-01','B103'),
-- Economics (dept 3)
(3,'Khaled',  'Ibrahim',    'Prof.',       'Macroeconomics',             'k.ibrahim@cu.edu.eg',   '+20-111-0007','1993-09-01','C101'),
(3,'Dina',    'Salah',      'Dr.',         'Microeconomics',             'd.salah@cu.edu.eg',     '+20-111-0008','2005-09-01','C102'),
-- Statistics (dept 4)
(4,'Mona',    'Gamal',      'Prof.',       'Applied Statistics',         'm.gamal@cu.edu.eg',     '+20-111-0009','1997-09-01','D101'),
(4,'Sherif',  'Ramadan',    'Dr.',         'Operations Research',        's.ramadan@cu.edu.eg',   '+20-111-0010','2011-09-01','D102'),
-- Marketing (dept 5)
(5,'Tarek',   'Samir',      'Prof.',       'Consumer Behaviour',         't.samir@cu.edu.eg',     '+20-111-0011','2000-09-01','E101'),
(5,'Heba',    'Mostafa',    'Dr.',         'Digital Marketing',          'h.mostafa@cu.edu.eg',   '+20-111-0012','2013-09-01','E102'),
-- Finance (dept 6)
(6,'Rania',   'Adel',       'Prof.',       'Corporate Finance',          'r.adel@cu.edu.eg',      '+20-111-0013','1999-09-01','F101'),
(6,'Wael',    'Othman',     'Assoc. Prof.','Investment Analysis',        'w.othman@cu.edu.eg',    '+20-111-0014','2007-09-01','F102');


-- ============================================================
-- 5. COURSES
-- ============================================================
CREATE TABLE Courses (
    course_id       VARCHAR(255)    PRIMARY KEY,   -- e.g. ACC101
    dept_id         INTEGER NOT NULL REFERENCES Departments(dept_id),
    year_level      INTEGER NOT NULL REFERENCES AcademicYears(year_level),
    instructor_id   INTEGER NOT NULL REFERENCES Instructors(instructor_id),
    name            VARCHAR(255)    NOT NULL,
    credit_hours    INTEGER NOT NULL,
    semester        VARCHAR(255)    NOT NULL,      -- 'Fall' / 'Spring'
    max_capacity    INTEGER DEFAULT 40,
    description     VARCHAR(255)
);

INSERT INTO Courses VALUES
-- ── YEAR 1 ─────────────────────────────────────────────────
('ACC101',1,1,1,'Principles of Accounting I',        3,'Fall',  40,'Intro to double-entry bookkeeping'),
('ACC102',1,1,1,'Principles of Accounting II',       3,'Spring',40,'Trial balance, financial statements'),
('ECO101',3,1,7,'Introduction to Economics',         3,'Fall',  40,'Supply, demand, market equilibrium'),
('ECO102',3,1,8,'Microeconomics',                    3,'Spring',40,'Consumer & producer theory'),
('STA101',4,1,9,'Business Mathematics',              3,'Fall',  40,'Algebra, calculus foundations'),
('STA102',4,1,9,'Introduction to Statistics',        3,'Spring',40,'Descriptive statistics & probability'),
('BUS101',2,1,4,'Introduction to Business',          3,'Fall',  40,'Business environment & functions'),
('BUS102',2,1,5,'Principles of Management',          3,'Spring',40,'Planning, organising, leading, controlling'),
-- ── YEAR 2 ─────────────────────────────────────────────────
('ACC201',1,2,2,'Financial Accounting',              3,'Fall',  40,'IFRS-based financial reporting'),
('ACC202',1,2,3,'Cost Accounting',                   3,'Spring',40,'Product costing, CVP analysis'),
('ECO201',3,2,7,'Macroeconomics',                    3,'Fall',  40,'National income, monetary & fiscal policy'),
('ECO202',3,2,8,'Money & Banking',                   3,'Spring',40,'Financial institutions & monetary system'),
('STA201',4,2,9,'Statistics for Business',           3,'Fall',  40,'Inference, regression, ANOVA'),
('STA202',4,2,10,'Operations Research I',            3,'Spring',40,'Linear programming, simplex method'),
('MKT201',5,2,11,'Principles of Marketing',          3,'Fall',  40,'4 Ps, segmentation, targeting'),
('FIN201',6,2,13,'Introduction to Finance',          3,'Spring',40,'TVM, risk & return basics'),
-- ── YEAR 3 ─────────────────────────────────────────────────
('ACC301',1,3,2,'Auditing & Assurance',              3,'Fall',  35,'Audit standards, internal control'),
('ACC302',1,3,1,'Advanced Financial Accounting',     3,'Spring',35,'Consolidations, forex transactions'),
('FIN301',6,3,13,'Corporate Finance',                3,'Fall',  35,'Capital structure, WACC, valuation'),
('FIN302',6,3,14,'Investment Analysis',              3,'Spring',35,'Portfolio theory, CAPM, securities'),
('MKT301',5,3,11,'Consumer Behaviour',               3,'Fall',  35,'Decision making, culture, perception'),
('MKT302',5,3,12,'Digital Marketing',                3,'Spring',35,'SEO, social media, e-commerce'),
('BUS301',2,3,4,'Strategic Management',              3,'Fall',  35,'SWOT, competitive analysis, strategy'),
('BUS302',2,3,5,'Human Resource Management',         3,'Spring',35,'Recruitment, training, performance'),
-- ── YEAR 4 ─────────────────────────────────────────────────
('ACC401',1,4,2,'Advanced Auditing',                 3,'Fall',  30,'Forensic accounting, fraud detection'),
('ACC402',1,4,3,'Tax Accounting',                    3,'Spring',30,'Egyptian tax law, VAT, income tax'),
('FIN401',6,4,13,'Financial Markets',                3,'Fall',  30,'Stock exchange, derivatives, risk mgmt'),
('FIN402',6,4,14,'Islamic Finance',                  3,'Spring',30,'Sukuk, Murabaha, Musharakah'),
('MKT401',5,4,11,'International Marketing',          3,'Fall',  30,'Global strategies, export marketing'),
('BUS401',2,4,4,'Business Ethics & Governance',      3,'Fall',  30,'CSR, board governance, compliance'),
('RES401',4,4,9,'Research Methods & Graduation Project',4,'Spring',30,'Thesis writing, quantitative & qualitative methods');


-- ============================================================
-- 6. COURSE PREREQUISITES
-- ============================================================
CREATE TABLE CoursePrerequisites (
    course_id   VARCHAR(255) REFERENCES Courses(course_id),
    prereq_id   VARCHAR(255) REFERENCES Courses(course_id),
    PRIMARY KEY (course_id, prereq_id)
);

INSERT INTO CoursePrerequisites VALUES
('ACC102','ACC101'),
('ACC201','ACC102'),
('ACC202','ACC201'),
('ACC301','ACC202'),
('ACC302','ACC301'),
('ACC401','ACC301'),
('ACC402','ACC302'),
('ECO202','ECO101'),
('ECO201','ECO102'),
('STA201','STA102'),
('STA202','STA201'),
('FIN201','ECO102'),
('FIN301','FIN201'),
('FIN302','FIN301'),
('FIN401','FIN302'),
('FIN402','FIN301'),
('MKT301','MKT201'),
('MKT302','MKT201'),
('MKT401','MKT301'),
('BUS301','BUS102'),
('BUS302','BUS101'),
('RES401','STA201');


-- ============================================================
-- 7. STUDENTS  (20 per year level = 80 total)
-- ============================================================
CREATE TABLE Students (
    student_id      VARCHAR(255)    PRIMARY KEY,   -- e.g. COM2024001
    dept_id         INTEGER NOT NULL REFERENCES Departments(dept_id),
    year_level      INTEGER NOT NULL REFERENCES AcademicYears(year_level),
    first_name      VARCHAR(255)    NOT NULL,
    last_name       VARCHAR(255)    NOT NULL,
    gender          VARCHAR(255)    CHECK(gender IN ('M','F')),
    date_of_birth   VARCHAR(255),
    national_id     VARCHAR(255)    UNIQUE,
    email           VARCHAR(255)    UNIQUE,
    phone           VARCHAR(255),
    address         VARCHAR(255),
    enrollment_date VARCHAR(255),
    status          VARCHAR(255)    DEFAULT 'Active' CHECK(status IN ('Active','Suspended','Graduated','Withdrawn')),
    gpa             REAL    DEFAULT 0.0,
    total_credits   INTEGER DEFAULT 0,
    scholarship     VARCHAR(255)    DEFAULT 'None'
);

-- ── YEAR 1 (20 students, enrolled 2024) ─────────────────────
INSERT INTO Students VALUES
('COM2024001',1,1,'Mohamed',   'Ahmed El-Sherif', 'M','2005-03-12','30503120011001','m.ahmed2024@commerce.cu.edu.eg',    '+20-100-1001001','12 Tahrir St, Cairo',        '2024-09-15','Active',0.0,0,'None'),
('COM2024002',1,1,'Nour',      'Khaled Mansour',  'F','2005-07-25','30507250011002','n.khaled2024@commerce.cu.edu.eg',   '+20-100-1001002','5 Zamalek Ave, Cairo',       '2024-09-15','Active',0.0,0,'Merit'),
('COM2024003',2,1,'Omar',      'Youssef Farouk',  'M','2005-01-08','30501080011003','o.youssef2024@commerce.cu.edu.eg',  '+20-100-1001003','78 Heliopolis Rd, Cairo',    '2024-09-15','Active',0.0,0,'None'),
('COM2024004',3,1,'Salma',     'Ibrahim Naguib',  'F','2005-11-30','30511300011004','s.ibrahim2024@commerce.cu.edu.eg',  '+20-100-1001004','33 Nasr City, Cairo',        '2024-09-15','Active',0.0,0,'None'),
('COM2024005',5,1,'Karim',     'Hassan Tantawi',  'M','2005-06-17','30506170011005','k.hassan2024@commerce.cu.edu.eg',   '+20-100-1001005','22 Maadi Corniche, Cairo',   '2024-09-15','Active',0.0,0,'None'),
('COM2024006',6,1,'Yasmin',    'Adel Ramadan',    'F','2005-04-02','30504020011006','y.adel2024@commerce.cu.edu.eg',     '+20-100-1001006','9 Dokki St, Giza',           '2024-09-15','Active',0.0,0,'Merit'),
('COM2024007',1,1,'Ahmed',     'Samy El-Naggar',  'M','2005-09-22','30509220011007','a.samy2024@commerce.cu.edu.eg',     '+20-100-1001007','44 Shubra, Cairo',           '2024-09-15','Active',0.0,0,'None'),
('COM2024008',2,1,'Hana',      'Mostafa Zaki',    'F','2005-02-14','30502140011008','h.mostafa2024@commerce.cu.edu.eg',  '+20-100-1001008','17 Mohandessin, Giza',       '2024-09-15','Active',0.0,0,'None'),
('COM2024009',3,1,'Ziad',      'Walid El-Masry',  'M','2005-08-05','30508050011009','z.walid2024@commerce.cu.edu.eg',    '+20-100-1001009','61 Imbaba, Giza',            '2024-09-15','Active',0.0,0,'None'),
('COM2024010',4,1,'Mariam',    'Tarek Fouad',     'F','2005-05-19','30505190011010','m.tarek2024@commerce.cu.edu.eg',    '+20-100-1001010','3 New Cairo, Cairo',         '2024-09-15','Active',0.0,0,'Merit'),
('COM2024011',5,1,'Bassem',    'Ramy Selim',      'M','2005-10-11','30510110011011','b.ramy2024@commerce.cu.edu.eg',     '+20-100-1001011','88 6th October, Giza',       '2024-09-15','Active',0.0,0,'None'),
('COM2024012',6,1,'Rana',      'Ashraf Habib',    'F','2005-12-28','30512280011012','r.ashraf2024@commerce.cu.edu.eg',   '+20-100-1001012','25 Agouza, Giza',            '2024-09-15','Active',0.0,0,'None'),
('COM2024013',1,1,'Hamza',     'Fawzi Osman',     'M','2005-07-03','30507030011013','h.fawzi2024@commerce.cu.edu.eg',    '+20-100-1001013','14 Madinet Nasr, Cairo',     '2024-09-15','Active',0.0,0,'None'),
('COM2024014',2,1,'Sara',      'Nabil Gohar',     'F','2005-03-27','30503270011014','s.nabil2024@commerce.cu.edu.eg',    '+20-100-1001014','56 Ain Shams, Cairo',        '2024-09-15','Active',0.0,0,'None'),
('COM2024015',3,1,'Mahmoud',   'Essam Badr',      'M','2006-01-15','30601150011015','m.essam2024@commerce.cu.edu.eg',    '+20-100-1001015','30 Bab El-Louk, Cairo',      '2024-09-15','Active',0.0,0,'Merit'),
('COM2024016',4,1,'Dalia',     'Khaled Sorour',   'F','2005-08-20','30508200011016','d.khaled2024@commerce.cu.edu.eg',   '+20-100-1001016','71 Sporting, Alexandria',    '2024-09-15','Active',0.0,0,'None'),
('COM2024017',5,1,'Amr',       'Hassan El-Badawi','M','2005-04-14','30504140011017','a.hassan2024@commerce.cu.edu.eg',   '+20-100-1001017','19 Smouha, Alexandria',      '2024-09-15','Active',0.0,0,'None'),
('COM2024018',6,1,'Noha',      'Gamal Ismail',    'F','2005-06-09','30506090011018','n.gamal2024@commerce.cu.edu.eg',    '+20-100-1001018','42 Sidi Gaber, Alexandria',  '2024-09-15','Active',0.0,0,'None'),
('COM2024019',1,1,'Youssef',   'Hesham Abdelaziz','M','2005-11-01','30511010011019','y.hesham2024@commerce.cu.edu.eg',   '+20-100-1001019','8 Mansoura, Dakahlia',       '2024-09-15','Active',0.0,0,'None'),
('COM2024020',2,1,'Nada',      'Sameh Ghoneim',   'F','2005-02-23','30502230011020','n.sameh2024@commerce.cu.edu.eg',    '+20-100-1001020','53 Tanta, Gharbia',          '2024-09-15','Active',0.0,0,'Merit');

-- ── YEAR 2 (20 students, enrolled 2023) ─────────────────────
INSERT INTO Students VALUES
('COM2023001',1,2,'Ibrahim',   'Mahmoud Saad',    'M','2004-03-10','30403100021001','i.mahmoud2023@commerce.cu.edu.eg',  '+20-100-1002001','20 Zamalek, Cairo',          '2023-09-15','Active',2.85,30,'None'),
('COM2023002',2,2,'Aya',       'Mohamed Rafaat',  'F','2004-07-18','30407180021002','a.mohamed2023@commerce.cu.edu.eg',  '+20-100-1002002','14 Heliopolis, Cairo',       '2023-09-15','Active',3.10,30,'Merit'),
('COM2023003',3,2,'Mostafa',   'Sayed El-Gohary', 'M','2004-01-25','30401250021003','m.sayed2023@commerce.cu.edu.eg',    '+20-100-1002003','9 Nasr City, Cairo',         '2023-09-15','Active',2.70,30,'None'),
('COM2023004',5,2,'Rawan',     'Adel Taha',       'F','2004-09-14','30409140021004','r.adel2023@commerce.cu.edu.eg',     '+20-100-1002004','35 Dokki, Giza',             '2023-09-15','Active',3.40,30,'Excellence'),
('COM2023005',6,2,'Tarek',     'Nour El-Din',     'M','2004-05-07','30405070021005','t.nour2023@commerce.cu.edu.eg',     '+20-100-1002005','67 Mohandessin, Giza',       '2023-09-15','Active',2.90,30,'None'),
('COM2023006',1,2,'Asmaa',     'Yasser Abou-Ali', 'F','2004-11-22','30411220021006','a.yasser2023@commerce.cu.edu.eg',   '+20-100-1002006','11 Maadi, Cairo',            '2023-09-15','Active',2.60,30,'None'),
('COM2023007',2,2,'Khaled',    'Ehab Gaber',      'M','2004-04-16','30404160021007','k.ehab2023@commerce.cu.edu.eg',     '+20-100-1002007','5 Shubra El-Kheima, Cairo',  '2023-09-15','Active',3.20,30,'Merit'),
('COM2023008',3,2,'Menna',     'Farouk Hamdan',   'F','2004-08-30','30408300021008','m.farouk2023@commerce.cu.edu.eg',   '+20-100-1002008','28 6th October, Giza',       '2023-09-15','Active',3.00,30,'None'),
('COM2023009',4,2,'Amira',     'Hany El-Sheikh',  'F','2004-02-11','30402110021009','a.hany2023@commerce.cu.edu.eg',     '+20-100-1002009','44 Agouza, Giza',            '2023-09-15','Active',3.55,30,'Excellence'),
('COM2023010',5,2,'Sherif',    'Tamer Hegazy',    'M','2004-06-05','30406050021010','s.tamer2023@commerce.cu.edu.eg',    '+20-100-1002010','90 New Cairo, Cairo',        '2023-09-15','Active',2.75,30,'None'),
('COM2023011',6,2,'Nourhan',   'Walid Osman',     'F','2004-10-19','30410190021011','n.walid2023@commerce.cu.edu.eg',    '+20-100-1002011','16 Bab El-Louk, Cairo',      '2023-09-15','Active',3.15,30,'Merit'),
('COM2023012',1,2,'Abdelrahman','Samir Khalifa',  'M','2004-12-08','30412080021012','ab.samir2023@commerce.cu.edu.eg',   '+20-100-1002012','72 Imbaba, Giza',            '2023-09-15','Active',2.50,30,'None'),
('COM2023013',2,2,'Hoda',      'Ibrahim Zakaria', 'F','2004-07-27','30407270021013','h.ibrahim2023@commerce.cu.edu.eg',  '+20-100-1002013','34 Madinet Nasr, Cairo',     '2023-09-15','Active',2.95,30,'None'),
('COM2023014',3,2,'Ahmed',     'Kamal El-Rashidy','M','2004-03-03','30403030021014','a.kamal2023@commerce.cu.edu.eg',    '+20-100-1002014','58 Ain Shams, Cairo',        '2023-09-15','Active',2.80,30,'None'),
('COM2023015',4,2,'Shimaa',    'Ramzy Badran',    'F','2004-09-21','30409210021015','sh.ramzy2023@commerce.cu.edu.eg',   '+20-100-1002015','23 Smouha, Alexandria',      '2023-09-15','Active',3.30,30,'Merit'),
('COM2023016',5,2,'Hassan',    'Magdy El-Wakil',  'M','2004-01-14','30401140021016','h.magdy2023@commerce.cu.edu.eg',    '+20-100-1002016','7 Gleem, Alexandria',        '2023-09-15','Active',2.65,30,'None'),
('COM2023017',6,2,'Doaa',      'Osama Metwally',  'F','2004-06-29','30406290021017','d.osama2023@commerce.cu.edu.eg',    '+20-100-1002017','45 Sidi Gaber, Alexandria',  '2023-09-15','Active',3.05,30,'None'),
('COM2023018',1,2,'Hazem',     'Sabri Mansour',   'M','2004-04-17','30404170021018','h.sabri2023@commerce.cu.edu.eg',    '+20-100-1002018','29 Mansoura, Dakahlia',      '2023-09-15','Active',2.40,30,'None'),
('COM2023019',2,2,'Esraa',     'Gamal Barakat',   'F','2004-11-05','30411050021019','e.gamal2023@commerce.cu.edu.eg',    '+20-100-1002019','81 Tanta, Gharbia',          '2023-09-15','Active',2.90,30,'None'),
('COM2023020',3,2,'Mahmoud',   'Ali El-Hawary',   'M','2004-08-12','30408120021020','m.ali2023@commerce.cu.edu.eg',      '+20-100-1002020','60 Luxor, Upper Egypt',      '2023-09-15','Active',3.10,30,'Merit');

-- ── YEAR 3 (20 students, enrolled 2022) ─────────────────────
INSERT INTO Students VALUES
('COM2022001',1,3,'Sara',      'Ahmed El-Deeb',   'F','2003-04-05','30304050031001','s.ahmed2022@commerce.cu.edu.eg',    '+20-100-1003001','50 Zamalek, Cairo',          '2022-09-15','Active',3.20,62,'Merit'),
('COM2022002',2,3,'Fady',      'Mina Wahba',      'M','2003-08-13','30308130031002','f.mina2022@commerce.cu.edu.eg',     '+20-100-1003002','36 Heliopolis, Cairo',       '2022-09-15','Active',2.85,62,'None'),
('COM2022003',6,3,'Eman',      'Hossam Hafez',    'F','2003-02-20','30302200031003','e.hossam2022@commerce.cu.edu.eg',   '+20-100-1003003','18 Nasr City, Cairo',        '2022-09-15','Active',3.45,62,'Excellence'),
('COM2022004',4,3,'Karim',     'Sherif Moussa',   'M','2003-10-09','30310090031004','k.sherif2022@commerce.cu.edu.eg',   '+20-100-1003004','77 Dokki, Giza',             '2022-09-15','Active',2.70,62,'None'),
('COM2022005',5,3,'Marwa',     'Essam El-Sawy',   'F','2003-06-26','30306260031005','m.essam2022@commerce.cu.edu.eg',    '+20-100-1003005','41 Mohandessin, Giza',       '2022-09-15','Active',3.10,62,'Merit'),
('COM2022006',1,3,'Mostafa',   'Wael Abdel-Ghany','M','2003-12-14','30312140031006','m.wael2022@commerce.cu.edu.eg',     '+20-100-1003006','63 Maadi, Cairo',            '2022-09-15','Active',2.55,62,'None'),
('COM2022007',3,3,'Haidy',     'Omar Zohair',     'F','2003-03-31','30303310031007','h.omar2022@commerce.cu.edu.eg',     '+20-100-1003007','27 Shubra, Cairo',           '2022-09-15','Active',3.00,62,'None'),
('COM2022008',2,3,'Amr',       'Mahmoud Rizk',    'M','2003-07-16','30307160031008','a.mahmoud2022@commerce.cu.edu.eg',  '+20-100-1003008','5 6th October, Giza',        '2022-09-15','Active',2.90,62,'None'),
('COM2022009',6,3,'Heba',      'Ismail Nassar',   'F','2003-01-04','30301040031009','h.ismail2022@commerce.cu.edu.eg',   '+20-100-1003009','89 Agouza, Giza',            '2022-09-15','Active',3.60,62,'Excellence'),
('COM2022010',4,3,'Tarek',     'Fouad El-Araby',  'M','2003-05-22','30305220031010','t.fouad2022@commerce.cu.edu.eg',    '+20-100-1003010','12 New Cairo, Cairo',        '2022-09-15','Active',2.75,62,'None'),
('COM2022011',5,3,'Nour',      'Galal Barakat',   'F','2003-09-07','30309070031011','n.galal2022@commerce.cu.edu.eg',    '+20-100-1003011','34 Bab El-Louk, Cairo',      '2022-09-15','Active',3.35,62,'Merit'),
('COM2022012',1,3,'Bassam',    'Taha El-Guindy',  'M','2003-11-28','30311280031012','b.taha2022@commerce.cu.edu.eg',     '+20-100-1003012','55 Imbaba, Giza',            '2022-09-15','Active',2.40,62,'None'),
('COM2022013',3,3,'Reem',      'Ali Badawy',      'F','2003-04-17','30304170031013','r.ali2022@commerce.cu.edu.eg',      '+20-100-1003013','23 Madinet Nasr, Cairo',     '2022-09-15','Active',3.15,62,'Merit'),
('COM2022014',2,3,'Yehia',     'Nabil El-Shodery','M','2003-08-02','30308020031014','y.nabil2022@commerce.cu.edu.eg',    '+20-100-1003014','48 Ain Shams, Cairo',        '2022-09-15','Active',2.95,62,'None'),
('COM2022015',6,3,'Lobna',     'Hazem Sabra',     'F','2003-02-10','30302100031015','l.hazem2022@commerce.cu.edu.eg',    '+20-100-1003015','16 Smouha, Alexandria',      '2022-09-15','Active',3.25,62,'Merit'),
('COM2022016',4,3,'Ahmed',     'Saeed El-Kordy',  'M','2003-06-18','30306180031016','a.saeed2022@commerce.cu.edu.eg',    '+20-100-1003016','37 Gleem, Alexandria',       '2022-09-15','Active',2.80,62,'None'),
('COM2022017',5,3,'Samira',    'Raafat Shalaby',  'F','2003-10-24','30310240031017','s.raafat2022@commerce.cu.edu.eg',   '+20-100-1003017','74 Sidi Gaber, Alexandria',  '2022-09-15','Active',3.05,62,'None'),
('COM2022018',1,3,'Walid',     'Ihab El-Assal',   'M','2003-03-06','30303060031018','w.ihab2022@commerce.cu.edu.eg',     '+20-100-1003018','92 Mansoura, Dakahlia',      '2022-09-15','Active',2.65,62,'None'),
('COM2022019',2,3,'Ghada',     'Samy Barsoum',    'F','2003-07-11','30307110031019','g.samy2022@commerce.cu.edu.eg',     '+20-100-1003019','11 Tanta, Gharbia',          '2022-09-15','Active',2.85,62,'None'),
('COM2022020',3,3,'Mahmoud',   'Anwar El-Kenawy', 'M','2003-11-19','30311190031020','m.anwar2022@commerce.cu.edu.eg',    '+20-100-1003020','65 Assiut, Upper Egypt',     '2022-09-15','Active',3.40,62,'Merit');

-- ── YEAR 4 (20 students, enrolled 2021) ─────────────────────
INSERT INTO Students VALUES
('COM2021001',1,4,'Dina',      'Ramadan El-Sisi', 'F','2002-05-14','30205140041001','d.ramadan2021@commerce.cu.edu.eg',  '+20-100-1004001','3 Zamalek, Cairo',          '2021-09-15','Active',3.50,96,'Excellence'),
('COM2021002',6,4,'Wael',      'Atef El-Meligy',  'M','2002-09-22','30209220041002','w.atef2021@commerce.cu.edu.eg',     '+20-100-1004002','21 Heliopolis, Cairo',       '2021-09-15','Active',3.10,96,'Merit'),
('COM2021003',2,4,'Nadia',     'Medhat Barakat',   'F','2002-01-11','30201110041003','n.medhat2021@commerce.cu.edu.eg',   '+20-100-1004003','45 Nasr City, Cairo',        '2021-09-15','Active',2.80,96,'None'),
('COM2021004',5,4,'Hisham',    'Samir El-Sayed',  'M','2002-07-30','30207300041004','h.samir2021@commerce.cu.edu.eg',    '+20-100-1004004','67 Dokki, Giza',             '2021-09-15','Active',2.95,96,'None'),
('COM2021005',3,4,'Amal',      'Wagdy Tawfik',    'F','2002-03-25','30203250041005','a.wagdy2021@commerce.cu.edu.eg',    '+20-100-1004005','33 Mohandessin, Giza',       '2021-09-15','Active',3.30,96,'Merit'),
('COM2021006',4,4,'Hazem',     'Gamal El-Adl',    'M','2002-11-08','30211080041006','h.gamal2021@commerce.cu.edu.eg',    '+20-100-1004006','18 Maadi, Cairo',            '2021-09-15','Active',3.65,96,'Excellence'),
('COM2021007',1,4,'Mariam',    'Fathy El-Gendy',  'F','2002-06-17','30206170041007','m.fathy2021@commerce.cu.edu.eg',    '+20-100-1004007','82 Shubra, Cairo',           '2021-09-15','Active',2.75,96,'None'),
('COM2021008',2,4,'Tamer',     'Hussein Soliman',  'M','2002-02-04','30202040041008','t.hussein2021@commerce.cu.edu.eg',  '+20-100-1004008','14 6th October, Giza',       '2021-09-15','Active',3.20,96,'Merit'),
('COM2021009',6,4,'Layla',     'Ahmed El-Hennawy','F','2002-10-19','30210190041009','l.ahmed2021@commerce.cu.edu.eg',    '+20-100-1004009','56 Agouza, Giza',            '2021-09-15','Active',3.45,96,'Excellence'),
('COM2021010',3,4,'Samy',      'Ibrahim Zaki',    'M','2002-04-13','30204130041010','s.ibrahim2021@commerce.cu.edu.eg',  '+20-100-1004010','39 New Cairo, Cairo',        '2021-09-15','Active',2.60,96,'None'),
('COM2021011',5,4,'Hind',      'Nasser El-Badri', 'F','2002-08-27','30208270041011','h.nasser2021@commerce.cu.edu.eg',   '+20-100-1004011','71 Bab El-Louk, Cairo',      '2021-09-15','Active',3.15,96,'Merit'),
('COM2021012',1,4,'Kareem',    'Abdel-Hamid Rady','M','2002-12-06','30212060041012','k.abdel2021@commerce.cu.edu.eg',    '+20-100-1004012','26 Imbaba, Giza',            '2021-09-15','Active',2.50,96,'None'),
('COM2021013',4,4,'Nermeen',   'Talaat El-Halaby','F','2002-05-21','30205210041013','n.talaat2021@commerce.cu.edu.eg',   '+20-100-1004013','58 Madinet Nasr, Cairo',     '2021-09-15','Active',3.00,96,'None'),
('COM2021014',2,4,'Shady',     'Emad El-Gazar',   'M','2002-09-09','30209090041014','sh.emad2021@commerce.cu.edu.eg',   '+20-100-1004014','43 Ain Shams, Cairo',        '2021-09-15','Active',2.85,96,'None'),
('COM2021015',6,4,'Yara',      'Moneer El-Shazly','F','2002-03-03','30203030041015','y.moneer2021@commerce.cu.edu.eg',   '+20-100-1004015','29 Smouha, Alexandria',      '2021-09-15','Active',3.55,96,'Excellence'),
('COM2021016',3,4,'Ahmed',     'Rizk El-Mashad',  'M','2002-07-16','30207160041016','a.rizk2021@commerce.cu.edu.eg',    '+20-100-1004016','84 Gleem, Alexandria',       '2021-09-15','Active',2.70,96,'None'),
('COM2021017',5,4,'Ghada',     'Nagib Farag',     'F','2002-01-28','30201280041017','g.nagib2021@commerce.cu.edu.eg',    '+20-100-1004017','17 Sidi Gaber, Alexandria',  '2021-09-15','Active',3.25,96,'Merit'),
('COM2021018',4,4,'Mohamed',   'Fouad El-Masry',  'M','2002-11-15','30211150041018','m.fouad2021@commerce.cu.edu.eg',    '+20-100-1004018','53 Mansoura, Dakahlia',      '2021-09-15','Active',2.90,96,'None'),
('COM2021019',1,4,'Randa',     'Adly Mansour',    'F','2002-06-08','30206080041019','r.adly2021@commerce.cu.edu.eg',     '+20-100-1004019','76 Tanta, Gharbia',          '2021-09-15','Active',3.10,96,'Merit'),
('COM2021020',2,4,'Omar',      'Khattab Selim',   'M','2002-08-23','30208230041020','o.khattab2021@commerce.cu.edu.eg',  '+20-100-1004020','32 Aswan, Upper Egypt',      '2021-09-15','Active',2.75,96,'None');


-- ============================================================
-- 8. ENROLLMENTS
-- ============================================================
CREATE TABLE Enrollments (
    enrollment_id   INTEGER PRIMARY KEY AUTO_INCREMENT,
    student_id      VARCHAR(255)    NOT NULL REFERENCES Students(student_id),
    course_id       VARCHAR(255)    NOT NULL REFERENCES Courses(course_id),
    semester        VARCHAR(255)    NOT NULL,
    academic_year   VARCHAR(255)    NOT NULL,
    enrollment_date VARCHAR(255)    NOT NULL,
    status          VARCHAR(255)    DEFAULT 'Enrolled' CHECK(status IN ('Enrolled','Dropped','Completed','Failed')),
    UNIQUE(student_id, course_id, academic_year)
);

-- Year 1 students enrolled in Year 1 Fall courses
INSERT INTO Enrollments (student_id,course_id,semester,academic_year,enrollment_date,status)
SELECT s.student_id, c.course_id, 'Fall', '2024/2025', '2024-09-20', 'Enrolled'
FROM Students s, Courses c
WHERE s.year_level = 1 AND c.year_level = 1 AND c.semester = 'Fall';

-- Year 2 students enrolled in Year 2 Fall courses
INSERT INTO Enrollments (student_id,course_id,semester,academic_year,enrollment_date,status)
SELECT s.student_id, c.course_id, 'Fall', '2024/2025', '2024-09-20', 'Enrolled'
FROM Students s, Courses c
WHERE s.year_level = 2 AND c.year_level = 2 AND c.semester = 'Fall';

-- Year 3 students enrolled in Year 3 Fall courses
INSERT INTO Enrollments (student_id,course_id,semester,academic_year,enrollment_date,status)
SELECT s.student_id, c.course_id, 'Fall', '2024/2025', '2024-09-20', 'Enrolled'
FROM Students s, Courses c
WHERE s.year_level = 3 AND c.year_level = 3 AND c.semester = 'Fall';

-- Year 4 students enrolled in Year 4 Fall courses
INSERT INTO Enrollments (student_id,course_id,semester,academic_year,enrollment_date,status)
SELECT s.student_id, c.course_id, 'Fall', '2024/2025', '2024-09-20', 'Enrolled'
FROM Students s, Courses c
WHERE s.year_level = 4 AND c.year_level = 4 AND c.semester = 'Fall';


-- ============================================================
-- 9. GRADES
-- ============================================================
CREATE TABLE Grades (
    grade_id        INTEGER PRIMARY KEY AUTO_INCREMENT,
    enrollment_id   INTEGER NOT NULL REFERENCES Enrollments(enrollment_id),
    midterm_score   REAL    CHECK(midterm_score  BETWEEN 0 AND 30),
    final_score     REAL    CHECK(final_score    BETWEEN 0 AND 50),
    coursework_score REAL   CHECK(coursework_score BETWEEN 0 AND 20),
    total_score     REAL    GENERATED ALWAYS AS
                        (COALESCE(midterm_score,0)+COALESCE(final_score,0)+COALESCE(coursework_score,0)) STORED,
    letter_grade    VARCHAR(255),
    gpa_points      REAL,
    exam_date       VARCHAR(255),
    remarks         VARCHAR(255)
);

-- Grades for Year 2 students (completed Year 1)
INSERT INTO Grades (enrollment_id, midterm_score, final_score, coursework_score, letter_grade, gpa_points, exam_date, remarks)
SELECT e.enrollment_id,
    ROUND(18 + (FLOOR(RAND() * 12)), 1),
    ROUND(30 + (FLOOR(RAND() * 20)), 1),
    ROUND(12 + (FLOOR(RAND() * 8)),  1),
    CASE WHEN (18+30+12) >= 90 THEN 'A+'
         WHEN (18+30+12) >= 85 THEN 'A'
         WHEN (18+30+12) >= 80 THEN 'B+'
         WHEN (18+30+12) >= 75 THEN 'B'
         WHEN (18+30+12) >= 70 THEN 'C+'
         WHEN (18+30+12) >= 65 THEN 'C'
         WHEN (18+30+12) >= 60 THEN 'D'
         ELSE 'F' END,
    CASE WHEN (18+30+12) >= 90 THEN 4.0
         WHEN (18+30+12) >= 85 THEN 3.7
         WHEN (18+30+12) >= 80 THEN 3.3
         WHEN (18+30+12) >= 75 THEN 3.0
         WHEN (18+30+12) >= 70 THEN 2.7
         WHEN (18+30+12) >= 65 THEN 2.3
         WHEN (18+30+12) >= 60 THEN 2.0
         ELSE 0.0 END,
    '2024-01-15',
    'Fall 2023/2024 Final Exam'
FROM Enrollments e
JOIN Students s ON e.student_id = s.student_id
WHERE s.year_level = 2;

-- Grades for Year 3 students
INSERT INTO Grades (enrollment_id, midterm_score, final_score, coursework_score, letter_grade, gpa_points, exam_date, remarks)
SELECT e.enrollment_id,
    ROUND(20 + (FLOOR(RAND() * 10)), 1),
    ROUND(33 + (FLOOR(RAND() * 17)), 1),
    ROUND(14 + (FLOOR(RAND() * 6)),  1),
    'B', 3.0, '2024-01-15', 'Fall 2023/2024 Final Exam'
FROM Enrollments e
JOIN Students s ON e.student_id = s.student_id
WHERE s.year_level = 3;

-- Grades for Year 4 students
INSERT INTO Grades (enrollment_id, midterm_score, final_score, coursework_score, letter_grade, gpa_points, exam_date, remarks)
SELECT e.enrollment_id,
    ROUND(21 + (FLOOR(RAND() * 9)), 1),
    ROUND(34 + (FLOOR(RAND() * 16)), 1),
    ROUND(15 + (FLOOR(RAND() * 5)),  1),
    'B+', 3.3, '2024-01-15', 'Fall 2023/2024 Final Exam'
FROM Enrollments e
JOIN Students s ON e.student_id = s.student_id
WHERE s.year_level = 4;


-- ============================================================
-- 10. USERS (Login Credentials)
-- ============================================================
CREATE TABLE FacUsers (
    user_id     VARCHAR(255) PRIMARY KEY,
    email       VARCHAR(255) UNIQUE,
    password    VARCHAR(255)
);

-- Create a login account for every student email
INSERT INTO FacUsers (user_id, email, password)
SELECT
    student_id,
    email,
    'password123'
FROM Students
WHERE email IS NOT NULL;

-- Create a login account for every instructor email
INSERT INTO FacUsers (user_id, email, password)
SELECT
    'INS' || instructor_id,
    email,
    'password123'
FROM Instructors
WHERE email IS NOT NULL;


-- ============================================================
-- 11. PAYMENTS (Tuition Fees)
-- ============================================================
CREATE TABLE FacPayments (
    payment_id      INTEGER PRIMARY KEY AUTO_INCREMENT,
    student_id      VARCHAR(255)    NOT NULL REFERENCES Students(student_id),
    academic_year   VARCHAR(255)    NOT NULL,
    amount_egp      REAL    NOT NULL,
    payment_date    VARCHAR(255)    NOT NULL,
    payment_method  VARCHAR(255)    CHECK(payment_method IN ('Bank Transfer','Cash','Online','Scholarship')),
    status          VARCHAR(255)    DEFAULT 'Paid' CHECK(status IN ('Paid','Pending','Overdue','Waived')),
    receipt_no      VARCHAR(255)    UNIQUE,
    notes           VARCHAR(255)
);

-- Generate payment records for all 80 students
INSERT INTO FacPayments (student_id, academic_year, amount_egp, payment_date, payment_method, status, receipt_no, notes)
SELECT
    student_id,
    CASE year_level
        WHEN 1 THEN '2024/2025'
        WHEN 2 THEN '2023/2024'
        WHEN 3 THEN '2022/2023'
        WHEN 4 THEN '2021/2022'
    END,
    CASE scholarship
        WHEN 'Excellence' THEN 0
        WHEN 'Merit'      THEN 3500
        ELSE 7000
    END,
    CASE year_level
        WHEN 1 THEN '2024-10-01'
        WHEN 2 THEN '2023-10-01'
        WHEN 3 THEN '2022-10-01'
        WHEN 4 THEN '2021-10-01'
    END,
    CASE scholarship
        WHEN 'Excellence' THEN 'Scholarship'
        WHEN 'Merit'      THEN 'Scholarship'
        ELSE 'Bank Transfer'
    END,
    CASE scholarship
        WHEN 'Excellence' THEN 'Waived'
        WHEN 'Merit'      THEN 'Paid'
        ELSE 'Paid'
    END,
    'RCP-' || student_id,
    CASE scholarship
        WHEN 'Excellence' THEN 'Full scholarship – fees waived'
        WHEN 'Merit'      THEN '50% merit scholarship applied'
        ELSE 'Full tuition paid'
    END
FROM Students;


-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- View 1: Full student profile
CREATE VIEW vw_StudentProfile AS
SELECT
    s.student_id,
    s.first_name || ' ' || s.last_name      AS full_name,
    s.gender,
    s.date_of_birth,
    ay.label                                 AS year_level,
    d.name                                   AS department,
    s.gpa,
    s.total_credits,
    s.scholarship,
    s.status,
    s.email,
    s.phone,
    s.address
FROM Students s
JOIN Departments   d  ON s.dept_id    = d.dept_id
JOIN AcademicYears ay ON s.year_level = ay.year_level;

-- View 2: Course roster with instructor
CREATE VIEW vw_CourseRoster AS
SELECT
    c.course_id,
    c.name                                   AS course_name,
    c.credit_hours,
    c.semester,
    ay.label                                 AS year_level,
    d.name                                   AS department,
    i.title || ' ' || i.first_name || ' ' || i.last_name AS instructor,
    i.email                                  AS instructor_email,
    COUNT(e.enrollment_id)                   AS enrolled_students
FROM Courses c
JOIN Departments   d  ON c.dept_id       = d.dept_id
JOIN AcademicYears ay ON c.year_level    = ay.year_level
JOIN Instructors   i  ON c.instructor_id = i.instructor_id
LEFT JOIN Enrollments e ON c.course_id   = e.course_id
GROUP BY c.course_id;

-- View 3: Grade report
CREATE VIEW vw_GradeReport AS
SELECT
    s.student_id,
    s.first_name || ' ' || s.last_name  AS student_name,
    c.course_id,
    c.name                               AS course_name,
    e.academic_year,
    g.midterm_score,
    g.final_score,
    g.coursework_score,
    g.total_score,
    g.letter_grade,
    g.gpa_points
FROM Grades g
JOIN Enrollments e ON g.enrollment_id = e.enrollment_id
JOIN Students    s ON e.student_id    = s.student_id
JOIN Courses     c ON e.course_id     = c.course_id;

-- View 4: Department statistics
CREATE VIEW vw_DeptStats AS
SELECT
    d.name                               AS department,
    COUNT(DISTINCT s.student_id)         AS total_students,
    COUNT(DISTINCT i.instructor_id)      AS total_instructors,
    COUNT(DISTINCT c.course_id)          AS total_courses,
    ROUND(AVG(s.gpa), 2)                 AS avg_gpa,
    COUNT(CASE WHEN s.scholarship != 'None' THEN 1 END) AS scholarship_holders
FROM Departments d
LEFT JOIN Students    s ON d.dept_id = s.dept_id
LEFT JOIN Instructors i ON d.dept_id = i.dept_id
LEFT JOIN Courses     c ON d.dept_id = c.dept_id
GROUP BY d.dept_id, d.name;

-- View 5: Payment summary
CREATE VIEW vw_PaymentSummary AS
SELECT
    p.payment_id,
    s.student_id,
    s.first_name || ' ' || s.last_name  AS student_name,
    s.year_level,
    p.academic_year,
    p.amount_egp,
    p.payment_method,
    p.payment_date,
    p.status                             AS payment_status,
    p.receipt_no
FROM FacPayments p
JOIN Students s ON p.student_id = s.student_id;


-- ============================================================
-- SAMPLE QUERIES (for reference)
-- ============================================================

-- Q1: All students in Year 2 with their GPA
-- SELECT full_name, department, gpa, scholarship FROM vw_StudentProfile WHERE year_level LIKE '%Second%' ORDER BY gpa DESC;

-- Q2: Top 5 students by GPA across all years
-- SELECT full_name, year_level, department, gpa FROM vw_StudentProfile ORDER BY gpa DESC LIMIT 5;

-- Q3: Course roster for Fall semester
-- SELECT course_id, course_name, year_level, instructor, enrolled_students FROM vw_CourseRoster WHERE semester = 'Fall';

-- Q4: Students with Excellence scholarship
-- SELECT full_name, year_level, department FROM vw_StudentProfile WHERE scholarship = 'Excellence';

-- Q5: Grade report for a specific student
-- SELECT course_name, academic_year, total_score, letter_grade, gpa_points FROM vw_GradeReport WHERE student_id = 'COM2023004';

-- Q6: Department statistics overview
-- SELECT * FROM vw_DeptStats ORDER BY total_students DESC;

-- Q7: Students who have not paid (pending)
-- SELECT student_name, year_level, academic_year, amount_egp, payment_status FROM vw_PaymentSummary WHERE payment_status = 'Pending';

-- Q8: Total revenue by academic year
-- SELECT academic_year, SUM(amount_egp) AS total_collected FROM FacPayments WHERE status = 'Paid' GROUP BY academic_year;

-- Q9: Count students by gender per department
-- SELECT department, SUM(CASE WHEN gender='M' THEN 1 ELSE 0 END) AS males, SUM(CASE WHEN gender='F' THEN 1 ELSE 0 END) AS females FROM vw_StudentProfile GROUP BY department;

-- Q10: Prerequisite chain for a course
-- SELECT c.course_id, c.name AS course, p.prereq_id, cr.name AS prerequisite FROM CoursePrerequisites p JOIN Courses c ON p.course_id = c.course_id JOIN Courses cr ON p.prereq_id = cr.course_id;

SET FOREIGN_KEY_CHECKS = 1;
