DEFINE ACCESS record_access ON DATABASE
  TYPE RECORD WITH JWT
  ALGORITHM HS512 KEY $SURREALDB_JWT_SECRET
  AUTHENTICATE {
    IF $auth.id {
      RETURN $auth.id;
    } ELSE IF $token.email {
      RETURN SELECT * FROM user WHERE email = $token.email;
    };
  }
  DURATION FOR TOKEN 24h, FOR SESSION 24h;
