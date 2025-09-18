SELECT score, count(id) FROM analytics GROUP BY score;

LET $bad = SELECT VALUE count FROM ONLY (
    SELECT score, count(id) FROM analytics WHERE score == 0 GROUP BY score
) LIMIT 1;
LET $good = SELECT VALUE count FROM only (
    SELECT score, count(id) FROM analytics WHERE score == 1 GROUP BY score
) LIMIT 1;

RETURN type::float($good||0) / type::float(($bad||0) + ($good||0));
