# Project notes LT

## Sesija 1 — Auth

Tikslas: suprasti register, login, password hash, access token, Bearer header, `get_current_user` ir `/auth/me`.

---

## Bendras auth flow

Šito projekto auth veikia taip:

1. Useris registruojasi su email ir password.
2. API patikrina, ar toks email dar neužimtas.
3. Password nėra saugomas paprastu tekstu.
4. Password paverčiamas į hash su `hash_password()`.
5. Useris išsaugomas DB.
6. Login metu API suranda userį pagal email.
7. API patikrina password su `verify_password()`.
8. Jei password teisingas, API sukuria access token su `create_access_token(user.id)`.
9. Frontend saugo tokeną.
10. Protected endpointams frontend siunčia tokeną per header:

```text
Authorization: Bearer <token>
```

11. Backend validuoja tokeną ir pagal jį nustato `current_user`.
12. Tada endpointas žino, kuris useris daro requestą.

Svarbu: dabar projekte naudojamas standartinis JWT Bearer token su HS256 per PyJWT.

---

## Registracija — `/auth/register`

Kai useris registruojasi, API gauna email ir password per `UserCreate` schema.

Pirma API patikrina, ar toks email jau yra DB:

- jei email jau yra, grąžina 400 klaidą: `Email already registered`
- jei email nėra, sukuria naują `User`

Slaptažodis nėra saugomas paprastu tekstu. Jis paverčiamas į hash su `hash_password()` ir saugomas kaip `hashed_password`.

Tada API padaro:

- `db.add(user)` — paruošia userį įrašymui
- `db.commit()` — įrašo į DB
- `db.refresh(user)` — atnaujina user objektą su DB sugeneruotu ID

Endpointas grąžina `UserRead`, todėl response turi user info, bet neturi password/hash.

---

## Login — `/auth/login`

Login gauna email ir password.

API suranda userį pagal email.

Jei userio nėra arba password netinka, grąžina 401.

Jei tinka, sukuria access token su:

```text
create_access_token(user.id)
```

Login response grąžina JWT access tokeną ir `token_type = bearer`.

---

## Access token

Tokenas saugo user ID kaip `sub`.

Tokenas turi:

- `sub` — user ID
- `iat` — kada tokenas sukurtas
- `exp` — kada tokenas baigia galioti

Tokenas pasirašomas su `SECRET_KEY`, todėl backend gali patikrinti, ar tokenas nebuvo pakeistas.

Šitas tokenas yra JWT Bearer token. JWT turi tris dalis:

```text
header.payload.signature
```

---

## Bearer header

Frontend siunčia tokeną taip:

```text
Authorization: Bearer <token>
```

Backend iš šito headerio paima tokeną, patikrina jį ir pagal user ID randa `current_user`.

---

## `/auth/me`

`/auth/me` naudoja `get_current_user`.

Jei tokenas validus, endpointas grąžina prisijungusį userį.

Jei tokeno nėra, jis blogas arba pasibaigęs, requestas nepraeina.

---

## `get_current_user`

Failas:

```text
app/dependencies.py
```

Šita funkcija naudojama protected endpointuose. Ji nustato, kuris useris daro requestą.

```python
bearer_scheme = HTTPBearer()
```

`HTTPBearer()` reiškia, kad FastAPI tikisi tokio headerio:

```text
Authorization: Bearer <token>
```

Kai endpointas turi:

```python
current_user: User = Depends(get_current_user)
```

FastAPI prieš vykdydamas endpointą pirmiausia paleidžia `get_current_user`.

Flow:

```text
FastAPI paima Authorization headerį.
HTTPBearer() iš jo ištraukia tokeną.
Pats tokenas pasiekiamas per credentials.credentials.
Tokenas tikrinamas su decode_access_token().
Jei tokenas blogas, pakeistas arba pasibaigęs, decode_access_token() grąžina None.
Jei tokenas geras, decode_access_token() grąžina user_id.
Tada useris ieškomas DB pagal ID su db.get(User, user_id).
Jei userio nėra arba jis neaktyvus, grąžinama 401.
Jei viskas gerai, funkcija grąžina userį kaip current_user.
```

Svarbi mintis:

Endpointai patys netikrina tokeno. Jie tiesiog parašo:

```python
current_user: User = Depends(get_current_user)
```

Ir FastAPI automatiškai pasirūpina, kad endpointas gautų prisijungusį userį.

Jei tokenas blogas, endpointo logika net nepradedama vykdyti.

Dar vienas niuansas: jei visai nėra `Authorization` headerio, klaidą pirmas gali grąžinti pats `HTTPBearer()`, dar prieš tavo `decode_access_token()`.

Jei headeris yra, bet tokenas blogas — tada tavo kodas grąžina:

```text
401 Invalid authentication token
```

Auth grandinė:

```text
register -> hash_password -> save user
login -> verify_password -> create_access_token
protected request -> HTTPBearer -> decode_access_token -> get user from DB -> current_user
```

---

## Auth kodo kelias

Register flow:

```text
/auth/register
-> app/routers/auth.py
-> register_user()
-> patikrina ar email neužimtas
-> hash_password()
-> išsaugo User DB
```

Login flow:

```text
/auth/login
-> app/routers/auth.py
-> login_user()
-> suranda User pagal email
-> verify_password()
-> create_access_token()
-> grąžina JWT access_token
```

Current user flow:

```text
/auth/me
-> app/routers/auth.py
-> read_current_user()
-> Depends(get_current_user)
-> app/dependencies.py
-> HTTPBearer paima tokeną iš Authorization headerio
-> decode_access_token()
-> db.get(User, user_id)
-> grąžina current_user
```

Trumpai:

```text
Register sukuria userį.
Login patikrina passwordą ir duoda JWT.
Protected endpointai per get_current_user patikrina tokeną ir gauna current_user.
```

---

## Sesija 2 — Sites ownership

Useris mato tik savo sites todėl, kad kiekvienas site turi `user_id`, kuris susiejamas su `current_user.id`.

Visi svarbūs `GET`, `PATCH`, `DELETE` ir event endpointai tikrina ownership pagal `Site.user_id == current_user.id`.

Jei site priklauso kitam useriui, backend jo neranda ir grąžina 404.

```text
Tokenas pasako, kas prisijungęs.
current_user.id pasako prisijungusio userio ID.
Site.user_id pasako, kam priklauso site.
Backend grąžina tik tuos sites, kur Site.user_id == current_user.id.
```

404 yra geresnis pasirinkimas tokiam projektui, nes jis neatskleidžia, ar svetimas site išvis egzistuoja.

Jei grąžintum `403 Forbidden`, tarsi pasakytum:

```text
Toks įrašas egzistuoja, bet tau negalima.
```

O su `404 Not Found` backend neatskleidžia, ar toks svetimas site egzistuoja.

```text
Site = objektas / darbas
Event = įrašas, kas su tuo site įvyko
```

---

## Sites ownership kodo kelias

Ownership tikrinimas yra centralizuotas per `get_user_site_or_404`.

Funkcija ieško site pagal du dalykus:

```text
Site.id == site_id
Site.user_id == current_user.id
```

Tai reiškia, kad svetimas site nėra randamas net jei useris žino jo ID.

Endpointai naudoja šitą funkciją:

```text
GET /sites/{site_id}
PATCH /sites/{site_id}
DELETE /sites/{site_id}
POST /sites/{site_id}/events
GET /sites/{site_id}/events
```

Jei site priklauso kitam useriui, `get_user_site_or_404` grąžina `404 Site not found`.

Tai apsaugo nuo:

- svetimų sites peržiūros
- svetimų sites keitimo
- svetimų sites trynimo
- eventų pridėjimo prie svetimo site
- svetimo site istorijos matymo

Trumpai:

```text
JWT pasako, kas prisijungęs.
current_user.id yra prisijungusio userio ID.
get_user_site_or_404 tikrina site_id + current_user.id.
Jei site svetimas, backend jo neranda ir grąžina 404.
```

---

## Sesija 3 — Events and status history

Add event leidžia prisijungusiam vartotojui pridėti įvykį prie savo site.

Backend pirmiausia patikrina, ar tas site priklauso tam vartotojui, ir tik tada išsaugo eventą.

List events parodo visus įvykius, priklausančius konkrečiam site.

Bet backend leidžia matyti tik tam useriui, kuriam priklauso pats site.

Kai vartotojas pakeičia site statusą, backend pats sukuria `status_change` eventą, kad istorijoje matytųsi, kada ir iš kokio statuso į kokį statusą buvo pakeista.

```text
Kiekvienas site turi savo įvykių istoriją.
Vartotojas gali rankiniu būdu pridėti eventus, pvz. pastabas.
Keičiant site statusą, backend automatiškai sukuria status_change eventą.
Visi event endpointai yra apsaugoti ir tikrina current_user.
Vartotojas gali matyti tik savo site įvykius.
```

Svarbu: event neturi atskiro `user_id`, nes jis priklauso site per `site_id`, o site jau turi `user_id`.

---

## Events ownership kodo kelias

Events endpointai naudoja `get_user_site_or_404`.

Prieš listinant arba kuriant eventą, backend pirmiausia patikrina, ar site priklauso prisijungusiam useriui.

Trumpai:

```text
JWT
-> current_user.id
-> get_user_site_or_404(site_id, current_user.id)
-> event logic
```

Jei site svetimas, backend grąžina `404 Site not found`, todėl eventų logika net nepradedama vykdyti.

---

## Sesija 4 — Docker and deploy

Dockerfile pasako Docker’iui, kaip paimti Python projektą, įdiegti dependencies ir paleisti FastAPI serverį.

Dockerfile tik paruošia aplikaciją paleidimui.

Docker Compose leidžia vienu metu paleisti backendą ir duomenų bazę kartu.

```text
Dockerfile = kaip pastatyti backend containerį
docker-compose = kaip paleisti backend + DB kartu lokaliai
```

Render paima projektą iš GitHub, paleidžia jį serveryje ir duoda viešą URL.

Neon yra production duomenų bazė, prie kurios jungiasi Render paleistas backend.

Pradžiai `/demo` neveikė production, nes `Dockerfile` trūko komandos:

```text
COPY frontend ./frontend
```

---

## Sesija 5 — Tests overview

Testai paleidžiami su:

```bash
pytest
```

arba per Docker:

```bash
docker compose exec api python -m pytest -q
```

`pytest` suranda testus `tests` folderyje, siunčia užklausas į FastAPI aplikaciją ir tikrina atsakymus, status kodus bei DB pakeitimus.

Sites testai patikrina, ar prisijungęs vartotojas gali kurti, matyti, keisti ir trinti tik savo sites.

Svetimi sites turi būti nematomi ir grąžinti 404.

Events testai tikrina site istoriją:

```text
Ar galima pridėti event prie savo site?
Ar galima gauti site events sąrašą?
Ar event pririštas prie teisingo site_id?
Ar negalima pridėti event prie svetimo site?
Ar svetimo site events grąžina 404?
```

Status change testas patikrina, ar keičiant site statusą backend automatiškai įrašo istorijos eventą.

Smoke testai nepatikrina visos logikos. Jie tik patikrina, ar app paleidžiamas ir pagrindiniai endpointai atsako.

```text
Auth = ar veikia prisijungimas ir tokenai.
Sites = ar useris valdo tik savo sites.
Events = ar site turi istoriją ir ji apsaugota.
Smoke = ar app ir DB apskritai gyvi.
```

---

## Sesija 6 — Testų supratimas

Tikslas: suprasti 5 svarbiausius testų tipus:

- auth
- site ownership
- pagination
- events
- smoke

Kiekvienam testui atsakau:

1. Ką testuoja?
2. Kokį bugą pagautų?
3. Kas būtų, jei testas dingtų?

---

## Auth testai

### Auth testas: `test_register_user`

Ką testuoja?

Patikrina, ar `/auth/register` sukuria naują userį, grąžina teisingus laukus ir negrąžina `hashed_password`.

Kokį bugą pagautų?

Pagautų, jei registracija neveiktų, useris nebūtų įrašomas į DB, slaptažodis būtų saugomas plain text arba API netyčia grąžintų `hashed_password`.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti rimto auth/security bugo: pvz. password būtų saugomas kaip paprastas tekstas arba response nutekintų hashą.

---

### Auth testas: `test_login_user`

Ką testuoja?

Patikrina, ar užregistruotas useris gali prisijungti su teisingu email ir password.

Kokį bugą pagautų?

Pagautų, jei login neveiktų, `verify_password()` blogai tikrintų slaptažodį arba API nesukurtų access tokeno.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad registracija veikia, bet prisijungti nebeįmanoma.

---

### Auth testas: `test_login_user_rejects_wrong_password`

Ką testuoja?

Patikrina, kad useris negali prisijungti su blogu passwordu.

Kokį bugą pagautų?

Pagautų, jei login per klaidą leistų prisijungti su neteisingu slaptažodžiu.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti kritinio security bugo, kur password tikrinimas neveikia.

---

### Auth testas: `test_login_user_rejects_unknown_email`

Ką testuoja?

Patikrina, kad neegzistuojantis email negali prisijungti.

Kokį bugą pagautų?

Pagautų, jei login kurtų tokeną neegzistuojančiam useriui arba neteisingai apdorotų nežinomą email.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad login logika leidžia prisijungti useriui, kurio nėra DB.

---

### Auth testas: `test_get_current_user_with_token`

Ką testuoja?

Patikrina, ar užregistruotas ir prisijungęs useris su valid JWT tokenu gali pasiekti `/auth/me`.

Kokį bugą pagautų?

Pagautų, jei login sukurtų blogą tokeną, jei `decode_access_token()` neveiktų, arba jei `get_current_user` nesugebėtų pagal tokeną rasti userio DB.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad login tokenas sukuriamas, bet protected endpointai su juo neveikia.

---

### Auth testas: `test_get_current_user_rejects_missing_token`

Ką testuoja?

Patikrina, kad `/auth/me` neveikia be `Authorization: Bearer <token>` headerio.

Kokį bugą pagautų?

Pagautų, jei protected endpointas netyčia būtų pasiekiamas be prisijungimo.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad privatus endpointas tapo viešas.

---

### Auth testas: `test_get_current_user_rejects_expired_token`

Ką testuoja?

Patikrina, kad pasibaigęs JWT tokenas nebeleidžia pasiekti `/auth/me`.

Kokį bugą pagautų?

Pagautų, jei backend ignoruotų `exp` lauką ir priimtų senus tokenus.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad seni tokenai galioja amžinai.

---

## Sites testai

### Sites testas: `test_create_and_list_sites`

Ką testuoja?

Patikrina, ar prisijungęs useris gali sukurti site ir po to jį matyti `/sites` sąraše.

Kokį bugą pagautų?

Pagautų, jei site nebūtų išsaugomas DB, jei response grąžintų blogus laukus arba jei list endpointas nerodytų sukurto site.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad pagrindinis site kūrimo ir listinimo flow nebeveikia.

---

### Sites testas: `test_update_site`

Ką testuoja?

Patikrina, ar prisijungęs useris gali pakeisti savo site statusą ir comment.

Kokį bugą pagautų?

Pagautų, jei `PATCH /sites/{id}` neveiktų, nekeistų statuso arba pakeistų ne tuos laukus.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad site statuso keitimas neveikia, nors demo vis dar gali atrodyti gyvas.

---

### Sites testas: `test_create_site_rejects_invalid_status`

Ką testuoja?

Patikrina, kad API neleidžia sukurti site su neegzistuojančiu statusu, pvz. `grybas`.

Kokį bugą pagautų?

Pagautų, jei schema arba enum validacija būtų sugadinta.

Kas būtų, jei testas dingtų?

Į DB galėtų patekti netvarkingi statusai, kurių frontend ar stats logika nemoka apdoroti.

---

## Ownership testai

### Ownership testas: `test_get_site_hides_other_users_site`

Ką testuoja?

Patikrina, kad user B negali pasiekti user A sukurto site pagal ID.

Kokį bugą pagautų?

Pagautų, jei backend ieškotų site tik pagal `site_id`, bet nepatikrintų, ar `site.user_id == current_user.id`.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti security bugo, kur vienas useris gali matyti kito userio objektus.

---

### Ownership testas: `test_update_site_hides_other_users_site`

Ką testuoja?

Patikrina, kad user B negali pakeisti user A site statuso.

Kokį bugą pagautų?

Pagautų, jei `PATCH /sites/{id}` tikrintų tik site ID, bet netikrintų savininko.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti bugo, kur vienas useris gali keisti svetimus objektus.

---

### Ownership testas: `test_delete_site_hides_other_users_site`

Ką testuoja?

Patikrina, kad user B negali ištrinti user A site.

Kokį bugą pagautų?

Pagautų, jei `DELETE /sites/{id}` leistų trinti pagal ID be `current_user` ownership patikros.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti kritinio bugo, kur vienas useris gali ištrinti svetimus duomenis.

---

### Ownership testas: `test_sites_stats_counts_only_current_user_sites`

Ką testuoja?

Patikrina, kad `/sites/stats` skaičiuoja tik prisijungusio userio sites, o ne visos DB sites.

Kokį bugą pagautų?

Pagautų, jei stats endpointas pamirštų filtruoti pagal `current_user.id`.

Kas būtų, jei testas dingtų?

Stats galėtų rodyti bendrus visų userių duomenis, kas būtų ir klaidinga, ir blogai dėl privatumo.

---

## Pagination testai

### Pagination testas: `test_list_sites_uses_limit_and_offset`

Ką testuoja?

Patikrina, ar `/sites` endpointas priima `limit` ir `offset` parametrus ir grąžina ribotą kiekį sites.

Kokį bugą pagautų?

Pagautų, jei backend ignoruotų `limit` / `offset` ir visada grąžintų visus sites.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad pagination neveikia, o API su daug duomenų pradėtų grąžinti per didelius response.

---

### Pagination testas: `test_list_sites_returns_pagination_metadata`

Ką testuoja?

Patikrina, ar `/sites` response grąžina ne tik `items`, bet ir pagination metadata: `total`, `limit`, `offset`.

Kokį bugą pagautų?

Pagautų, jei backend grąžintų sites sąrašą, bet pamestų informaciją, kiek iš viso yra įrašų ir kokie pagination parametrai buvo panaudoti.

Kas būtų, jei testas dingtų?

Frontendui būtų sunkiau rodyti puslapiavimą, nes jis nežinotų bendro įrašų kiekio.

---

### Pagination validation testai

Ką testuoja?

Patikrina, kad blogi pagination parametrai yra atmetami:

- `limit=0`
- `limit=101`
- `offset=-1`

Kokį bugą pagautų?

Pagautų, jei API leistų per mažą, per didelį arba neigiamą pagination parametrą.

Kas būtų, jei testai dingtų?

API galėtų priimti blogus parametrus, pvz. grąžinti per daug duomenų arba elgtis nenuspėjamai su neigiamu offset.

Trumpai:

```text
limit = kiek įrašų grąžinti
offset = kiek įrašų praleisti
items = konkretūs grąžinti sites
total = kiek iš viso yra sites pagal userį ir filtrus
```

---

## Pagination kodo kelias

`/sites` endpointas pradeda nuo query, kuris filtruoja pagal prisijungusį userį:

```text
Site.user_id == current_user.id
```

Tai reiškia, kad pagination ir `total` skaičiuojami tik current user sites, ne visos DB.

Pagination parametrai aprašyti taip:

```python
limit = Query(default=50, ge=1, le=100)
offset = Query(default=0, ge=0)
```

Todėl API automatiškai atmeta blogus parametrus:

- `limit=0`
- `limit=101`
- `offset=-1`

`total` suskaičiuojamas prieš `limit` ir `offset`, kad frontend žinotų, kiek iš viso yra įrašų.

Tada query pritaiko:

```text
order_by
limit
offset
```

Response grąžina:

- `total` — kiek iš viso yra įrašų pagal filtrą
- `limit` — kiek prašyta grąžinti
- `offset` — kiek praleista
- `items` — konkretūs grąžinti sites

Trumpai: `limit` pasako kiek paimti, `offset` pasako kiek praleisti, o `total` pasako kiek iš viso yra įrašų.

---

## Events testai

### Events testas: `test_create_and_list_site_events`

Ką testuoja?

Patikrina, ar prie savo site galima pridėti eventą ir po to jį matyti site events sąraše.

Kokį bugą pagautų?

Pagautų, jei eventas nebūtų išsaugomas DB, būtų pririštas prie blogo `site_id`, arba list endpointas jo negrąžintų.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad site istorijos funkcija neveikia.

---

### Events testas: `test_status_change_creates_site_event`

Ką testuoja?

Patikrina, kad pakeitus site statusą backend automatiškai sukuria `status_change` eventą.

Kokį bugą pagautų?

Pagautų, jei `PATCH /sites/{id}` pakeistų statusą, bet neįrašytų istorijos event’o.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad statuso istorija nebekaupiama.

---

### Events testas: `test_same_status_does_not_create_status_change_event`

Ką testuoja?

Patikrina, kad jei statusas nekeičiamas, `status_change` eventas nėra sukuriamas.

Kokį bugą pagautų?

Pagautų, jei backend kurtų nereikalingus istorijos įrašus net tada, kai statusas realiai nepasikeitė.

Kas būtų, jei testas dingtų?

Site istorijoje galėtų atsirasti netikri arba pertekliniai statuso pakeitimai.

---

### Events testas: `test_list_site_events_returns_pagination_metadata`

Ką testuoja?

Patikrina, ar events sąrašas grąžina `total`, `limit`, `offset` ir `items`.

Kokį bugą pagautų?

Pagautų, jei events pagination neveiktų arba response nebeturėtų pagination metadata.

Kas būtų, jei testas dingtų?

Frontendui būtų sunkiau rodyti site istoriją puslapiais.

---

### Events testas: `test_list_site_events_filters_by_event_type`

Ką testuoja?

Patikrina, ar galima filtruoti events pagal `event_type`, pvz. gauti tik `issue`.

Kokį bugą pagautų?

Pagautų, jei event type filtras būtų ignoruojamas ir API grąžintų visus eventus.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad site istorijos filtravimas neveikia.

---

## Events ownership testai

### Events ownership testas: `test_list_site_events_hides_other_users_site`

Ką testuoja?

Patikrina, kad user B negali matyti user A site eventų.

Kokį bugą pagautų?

Pagautų, jei events list endpointas tikrintų tik `site_id`, bet nepatikrintų, ar site priklauso `current_user`.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti security bugo, kur vienas useris gali matyti kito userio site istoriją.

---

### Events ownership testas: `test_create_site_event_hides_other_users_site`

Ką testuoja?

Patikrina, kad user B negali pridėti event prie user A site.

Kokį bugą pagautų?

Pagautų, jei backend leistų rašyti istorijos įrašus į svetimą site.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti kritinio bugo, kur useris gali gadinti kito userio site istoriją.

---

## Smoke testas

### Smoke testas: `scripts/smoke_test.py`

Ką testuoja?

Patikrina, ar visa aplikacija veikia per realius HTTP requestus:

- `/`
- `/health`
- register
- login
- sites
- filters
- sorting
- events
- stats

Kokį bugą pagautų?

Pagautų, jei aplikacija nepasileidžia, endpointai nepasiekiami, auth neveikia, JWT neveikia su protected endpointais, DB neveikia arba bazinis site/event flow sugriuvo.

Kas būtų, jei testas dingtų?

Galėtume nepastebėti, kad lokaliai arba production aplinkoje app paleista, bet pagrindinis naudotojo flow neveikia.

Smoke testas nėra skirtas visoms smulkmenoms patikrinti. Jis tik greitai pasako, ar pagrindinė sistema gyva.

---

## Smoke test kodo kelias

Smoke testas naudoja `BASE_URL`.

Default:

```text
http://localhost:8000
```

Galima paleisti ir prieš live API:

```bash
BASE_URL=https://ftth-task-tracker-api.onrender.com python scripts/smoke_test.py
```

Flow:

```text
GET /
GET /health
POST /auth/register
POST /auth/login
POST /sites su JWT
GET /sites su JWT
GET /sites su filters/sort
POST /sites/{id}/events su JWT
GET /sites/stats su JWT
```

Jei kuris nors requestas grąžina klaidą, smoke testas sustoja ir parodo, kuris endpointas failino.

Trumpai:

```text
Pytest testai tikrina konkrečią logiką ir edge cases.
Smoke testas tikrina, ar visa sistema realiai veikia kaip app.
```