# Aufgabe 1 – redis-cli Fingerübungen (echte Ausgaben)

Ausgeführt gegen Redis 7.0.15. Starten im Container: `docker exec -it RedisPraktikum2026 redis-cli`

Hinweise:
- `GETSET`, `RPOPLPUSH`, `BRPOPLPUSH` sind seit Redis 6.2 deprecated → `SET key val GET`, `LMOVE`, `BLMOVE`.
- `BRPOP mylist 1` liefert `(nil)` nach 1 s Timeout, weil die Liste zu dem Zeitpunkt leer war (blockierende Variante).
- `BITOP AND` von "abc" und "ABC" ergibt "ABC" (Kleinbuchstaben = Großbuchstaben + Bit 0x20).
- `BITFIELD ... INCRBY u8 0 100`: 200+100 = 300 → Überlauf (WRAP) → 44.
- Mengen (Sets) sind ungeordnet; die Reihenfolge bei SMEMBERS/SUNION kann abweichen.

```
127.0.0.1:6379> FLUSHALL
OK
127.0.0.1:6379> SET greeting "Hello"
OK
127.0.0.1:6379> APPEND greeting " Redis"
11
127.0.0.1:6379> GET greeting
Hello Redis
127.0.0.1:6379> STRLEN greeting
11
127.0.0.1:6379> GETRANGE greeting 0 4
Hello
127.0.0.1:6379> SETRANGE greeting 6 "World"
11
127.0.0.1:6379> GET greeting
Hello World
127.0.0.1:6379> SET counter 10
OK
127.0.0.1:6379> INCR counter
11
127.0.0.1:6379> INCRBY counter 5
16
127.0.0.1:6379> DECR counter
15
127.0.0.1:6379> DECRBY counter 3
12
127.0.0.1:6379> INCRBYFLOAT counter 0.5
12.5
127.0.0.1:6379> GETSET counter 0
12.5
127.0.0.1:6379> MSET k1 "a" k2 "b"
OK
127.0.0.1:6379> MGET k1 k2 nokey
a
b

127.0.0.1:6379> MSETNX k1 "x" k3 "c"
0
127.0.0.1:6379> SETNX k1 "y"
0
127.0.0.1:6379> SETEX temp 60 "tmp"
OK
127.0.0.1:6379> TTL temp
60
127.0.0.1:6379> PSETEX ptemp 5000 "ptmp"
OK
127.0.0.1:6379> PTTL ptemp
4997
127.0.0.1:6379> SETBIT bits 7 1
0
127.0.0.1:6379> GETBIT bits 7
1
127.0.0.1:6379> BITCOUNT bits
1
127.0.0.1:6379> BITPOS bits 1
7
127.0.0.1:6379> SET a "abc"
OK
127.0.0.1:6379> SET b "ABC"
OK
127.0.0.1:6379> BITOP AND res a b
3
127.0.0.1:6379> GET res
ABC
127.0.0.1:6379> BITFIELD bf SET u8 0 200 GET u8 0 INCRBY u8 0 100
0
200
44
127.0.0.1:6379> RPUSH mylist a b c
3
127.0.0.1:6379> LPUSH mylist z
4
127.0.0.1:6379> LRANGE mylist 0 -1
z
a
b
c
127.0.0.1:6379> LLEN mylist
4
127.0.0.1:6379> LINDEX mylist 1
a
127.0.0.1:6379> LINSERT mylist BEFORE c b2
5
127.0.0.1:6379> LSET mylist 0 Z
OK
127.0.0.1:6379> LREM mylist 1 b2
1
127.0.0.1:6379> LPUSHX nolist x
0
127.0.0.1:6379> RPUSHX mylist d
5
127.0.0.1:6379> LRANGE mylist 0 -1
Z
a
b
c
d
127.0.0.1:6379> LTRIM mylist 0 3
OK
127.0.0.1:6379> LPOP mylist
Z
127.0.0.1:6379> RPOP mylist
c
127.0.0.1:6379> RPOPLPUSH mylist otherlist
b
127.0.0.1:6379> LRANGE otherlist 0 -1
b
127.0.0.1:6379> BLPOP mylist 1
mylist
a
127.0.0.1:6379> BRPOP mylist 1

127.0.0.1:6379> BRPOPLPUSH otherlist mylist 1
b
127.0.0.1:6379> LRANGE mylist 0 -1
b
127.0.0.1:6379> SADD s1 a b c d
4
127.0.0.1:6379> SADD s2 c d e
3
127.0.0.1:6379> SCARD s1
4
127.0.0.1:6379> SISMEMBER s1 a
1
127.0.0.1:6379> SINTER s1 s2
d
c
127.0.0.1:6379> SUNION s1 s2
c
b
a
d
e
127.0.0.1:6379> SDIFF s1 s2
a
b
127.0.0.1:6379> SINTERSTORE s3 s1 s2
2
127.0.0.1:6379> SUNIONSTORE s4 s1 s2
5
127.0.0.1:6379> SDIFFSTORE s5 s1 s2
2
127.0.0.1:6379> SMOVE s1 s2 a
1
127.0.0.1:6379> SREM s2 e
1
127.0.0.1:6379> SMEMBERS s2
a
d
c
127.0.0.1:6379> SRANDMEMBER s4 2
b
d
127.0.0.1:6379> SPOP s5
b
127.0.0.1:6379> SSCAN s4 0 MATCH *
0
c
b
a
d
e

127.0.0.1:6379> HSET user:1 name "Ada" age 36 city "London"
3
127.0.0.1:6379> HGET user:1 name
Ada
127.0.0.1:6379> HMGET user:1 name city nofield
Ada
London

127.0.0.1:6379> HGETALL user:1
name
Ada
age
36
city
London
127.0.0.1:6379> HEXISTS user:1 age
1
127.0.0.1:6379> HINCRBY user:1 age 1
37
127.0.0.1:6379> HINCRBYFLOAT user:1 age 0.5
37.5
127.0.0.1:6379> HSETNX user:1 name "Bob"
0
127.0.0.1:6379> HSTRLEN user:1 name
3
127.0.0.1:6379> HKEYS user:1
name
age
city
127.0.0.1:6379> HVALS user:1
Ada
37.5
London
127.0.0.1:6379> HLEN user:1
3
127.0.0.1:6379> HDEL user:1 city
1
127.0.0.1:6379> HSCAN user:1 0
0
name
Ada
age
37.5
```
