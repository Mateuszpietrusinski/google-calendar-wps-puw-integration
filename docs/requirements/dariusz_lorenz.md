Problemem jest to, że wydarzenia na platformie wpadają randomowo i nie ma stałych godzin, w których się pojawiają. Czasem wydarzenia te są z godziny na godzinę (bo wykładowca się nagle obudził, że trzebaby zrobić wykład) - więc w synchronizacji musiałby występować częsty interwał sprawdzania, a sama technologia musiałaby być na tyle mało inwazyjna, by nie zostać przyblokowanym zbyt częstym odświeżaniem/wykonywaniem zapytań ( o ile platforma czy WPS ma taki mechanizm). 

Moim zdaniem w przypadku platformy: powinien być użyty eksport zaimplementowany tam (https://platforma.ahe.lodz.pl/calendar/export.php?) , z dość częstym interwałem (do np. 10 minut) - ten wytworzony plik ics powinien być importowany do kalendarza, ale z uprzednim checkiem, czy w kalendarzu czasem nie znajduje się wydarzenie o tym samym: tytule, godzinach trwania - wtedy powinien to pomijać by nie dublować wpisów z kalendarza. 

Co do WPS - tam nie ma mechanizmu, powinien być odczytany (jedyny eksport tam to pdf) i wrzucony po prostu w kalendarz. Tam interwał sprawdzania moze być inny - np. raz na 2-3 tygodnie - bo czasem coś zmieniają, ale jednak rzadko.

