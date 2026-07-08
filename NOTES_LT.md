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

### Registracija (register)

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


### Login

Login gauna email ir password.
API suranda userį pagal email.
Jei userio nėra arba password netinka, grąžina 401.
Jei tinka, sukuria access token su `create_access_token(user.id)`.

### Access token

Tokenas saugo user ID kaip `sub`.
Tokenas turi `iat` kada sukurtas ir `exp` kada baigiasi.
Tokenas pasirašomas su `SECRET_KEY`, todėl backend gali patikrinti, ar tokenas nebuvo pakeistas.

Šitas tokenas yra JWT Bearer token. JWT turi tris dalis: header, payload ir signature.

### Bearer header

Frontend siunčia tokeną taip:

Authorization: Bearer <token>

Backend iš šito headerio paima tokeną, patikrina jį ir pagal user ID randa current user.

### /auth/me

`/auth/me` naudoja `get_current_user`.
Jei tokenas validus, endpointas grąžina prisijungusį userį.
Jei tokeno nėra arba jis blogas, requestas nepraeina.

## `get_current_user`

Failas:

```text
app/dependencies.py
```

Šita funkcija naudojama protected endpointuose. Ji nustato, kuris useris daro requestą.
```
bearer_scheme = HTTPBearer()
```
HTTPBearer() reiškia, kad FastAPI tikisi tokio headerio:

Authorization: Bearer <token>

Kai endpointas turi:
```
current_user: User = Depends(get_current_user)
```
FastAPI prieš vykdydamas endpointą pirmiausia paleidžia get_current_user.

Flow
FastAPI paima Authorization headerį.
HTTPBearer() iš jo ištraukia tokeną.
Pats tokenas pasiekiamas per:
credentials.credentials
Tada tokenas tikrinamas:
user_id = decode_access_token(credentials.credentials)
Jei tokenas blogas, pakeistas arba pasibaigęs, decode_access_token() grąžina None.

Tada API grąžina klaidą:

raise HTTPException(status_code=401, detail="Invalid authentication token")
Jei tokenas geras, decode_access_token() grąžina user_id.
Tada useris ieškomas DB pagal ID:
user = db.get(User, user_id)
Jei userio nėra arba jis neaktyvus:
if user is None or not user.is_active:

API grąžina tą pačią klaidą:

Invalid authentication token
Jei viskas gerai, funkcija grąžina userį:
return user

Tada endpointas gauna šitą userį kaip current_user.

Svarbi mintis

Endpointai patys netikrina tokeno. Jie tiesiog parašo:

current_user: User = Depends(get_current_user)

Ir FastAPI automatiškai pasirūpina, kad endpointas gautų prisijungusį userį.

Jei tokenas blogas, endpointo logika net nepradedama vykdyti.


Dar vienas niuansas: jei **visai nėra** `Authorization` headerio, klaidą pirmas gali grąžinti pats `HTTPBearer()`, dar prieš tavo `decode_access_token()`. Jei headeris yra, bet tokenas blogas — tada tavo kodas grąžina `401 Invalid authentication token`.

Dabar auth grandinė pilna:

```text
register -> hash_password -> save user
login -> verify_password -> create_access_token
protected request -> HTTPBearer -> decode_access_token -> get user from DB -> current_user
```

## Sesija 2 — Sites ownership

Useris mato tik savo sites todėl, kad kiekvienas site turi `user_id`, kuris susiejamas su `current_user.id`. Visi `GET`, `PATCH`, `DELETE` endpointai filtruoja pagal `Site.user_id == current_user.id`. Jei site priklauso kitam useriui, backendas jo neranda ir grąžina 404.

```text
Tokenas pasako, kas prisijungęs.
current_user.id pasako jo ID.
Site.user_id pasako, kam priklauso site.
Backend grąžina tik tuos sites, kur Site.user_id == current_user.id.
```

404 yra geresnis pasirinkimas tokiam projektui, nes jis neatskleidžia, ar svetimas site išvis egzistuoja. Jei grąžintum: `403 Forbidden` tai tarsi pasakai: „Toks įrašas egzistuoja, bet tau negalima.“ O su `404 Not Found` backend neatskleidžia, ar toks svetimas site egzistuoja.

```text
Site = objektas / darbas
Event = įrašas, kas su tuo site įvyko
```
## Sesija 3 — Events and status history

Add event leidžia prisijungusiam vartotojui pridėti įvykį prie savo site. Backend pirmiausia patikrina, ar tas site priklauso tam vartotojui, ir tik tada išsaugo eventą.

List events parodo visus įvykius, priklausančius konkrečiam site. Bet backend leidžia matyti tik tam useriui, kuriam priklauso pats site.

Kai vartotojas pakeičia site statusą, backend pats sukuria `status_change` eventą, kad istorijoje matytųsi, kada ir iš kokio statuso į kokį statusą buvo pakeista.

```text
Kiekvienas site turi savo įvykių istoriją. Vartotojas gali rankiniu būdu pridėti eventus, pvz. pastabas, o keičiant site statusą backend automatiškai sukuria status_change eventą. Visi event endpointai yra apsaugoti ir tikrina current_user, todėl vartotojas gali matyti tik savo site įvykius.
```

## Sesija 4 — Docker and deploy

Dockerfile pasako Docker’iui, kaip paimti tavo Python projektą, įdiegti dependencies ir paleisti FastAPI serverį. Dockerfile tik paruošia tavo aplikaciją paleidimui.

Docker-compose leidžia vienu metu paleisti backendą ir duomenų bazę kartu.

```text
Dockerfile = kaip pastatyti backend containerį
docker-compose = kaip paleisti backend + DB kartu lokaliai
```

Render paima tavo projektą iš GitHub, paleidžia jį serveryje ir duoda viešą URL.

Neon yra production duomenų bazė prie kurios jungiasi Render paleistas backendas.

Pradžiai `/demo` neveikė production, nes `Dockerfile` trūko komandos `COPY frontend ./frontend`

## Sesija 5 — Tests

Testai paleidžiami su `pytest`. Jis suranda testus `tests` folderyje, siunčia užklausas į FastAPI aplikaciją ir tikrina atsakymus, `status` kodus bei DB pakeitimus.

Sites testai patikrina, ar prisijungęs vartotojas gali kurti, matyti, keisti ir trinti tik savo sites. Svetimi sites turi būti nematomi ir grąžinti 404.

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