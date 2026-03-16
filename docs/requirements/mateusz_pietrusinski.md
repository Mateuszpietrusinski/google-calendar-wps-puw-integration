# Integracja Kalendarza AHE (PUW & WPS) z Google Calendar

## 1. Definicja Problemu
Głównym wyzwaniem jest rozproszenie informacji o zajęciach i wydarzeniach akademickich. Obecnie studenci muszą manualnie sprawdzać wiele źródeł, co utrudnia efektywne zarządzanie czasem. Celem projektu jest umożliwienie studentom agregowania wszystkich kluczowych dat w jednym miejscu – ich prywatnym **Kalendarzu Google**, który będzie zawierał zarówno wydarzenia osobiste, jak i te publikowane na platformach **PUW** oraz **WPS**.

**Grupa docelowa:** Studenci Akademii Humanistyczno-Ekonomicznej (AHE).

---

## 2. Dlaczego? (Why)
Implementacja tego rozwiązania eliminuje szereg problemów, z którymi mierzą się studenci:
* **Oszczędność czasu:** Brak konieczności wielokrotnego logowania się do różnych serwisów w celu sprawdzenia harmonogramu.
* **Terminowość i organizacja:** Automatyczne przypomnienia zapobiegną przegapieniu terminów oddawania zadań oraz ułatwią dołączanie do zajęć online (obecny system PUW jest mało intuicyjny pod tym kątem).
* **Redukcja obciążenia poznawczego:** Planowanie zjazdów wymaga dziś korzystania z wielu platform jednocześnie. Integracja uprości ten proces, odciążając pamięć operacyjną użytkownika.

---

## 3. Co? (What)
Tworzymy narzędzie integrujące (konektor), dzięki któremu użytkownik platform PUW lub WPS będzie mógł:
1.  W prosty sposób przeprowadzić integrację między systemami uczelnianymi a kontem Google.
2.  Automatycznie pobierać dane o wydarzeniach i terminach.
3.  Synchronizować te informacje ze swoim prywatnym kalendarzem w czasie rzeczywistym.

---

## 4. Jak? (How)
Projekt zostanie zrealizowany jako oprogramowanie **Open Source**, które każdy użytkownik będzie mógł samodzielnie wdrożyć (hostować) na wybranej platformie.

### Założenia techniczne:
* **Autoryzacja:** Wykorzystanie standardu **OAuth 2.0** od Google dla zapewnienia bezpieczeństwa danych.
* **Pozyskiwanie danych:** * Weryfikacja dostępności oficjalnych API dla platform WPS i PUW.
    * W przypadku braku API – implementacja **scraper