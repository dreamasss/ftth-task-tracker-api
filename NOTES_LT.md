# Project notes draft LT

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

bearer_scheme = HTTPBearer()

HTTPBearer() reiškia, kad FastAPI tikisi tokio headerio:

Authorization: Bearer <token>

Kai endpointas turi:

current_user: User = Depends(get_current_user)

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
