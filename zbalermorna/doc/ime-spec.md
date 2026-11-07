# Zbalermorna IME Spec

IMEs should make the following conversions:

| input | c | unicode | description |
|-------|---|---------|-------------|
|  `p`  |  | `0xED80`| py |
|  `t`  |  | `0xED81`| ty |
|  `k`  |  | `0xED82`| ky |
|  `f`  |  | `0xED83`| fy |
|  `l`  |  | `0xED84`| ly |
|  `s`  |  | `0xED85`| sy |
|  `c`  |  | `0xED86`| cy |
|  `m`  |  | `0xED87`| my |
|  `x`  |  | `0xED88`| xy |
|  `.`  |  | `0xED89`| denpa bu |
|  `'`  |  | `0xED8A`| yhy |
|  `h`  |  | `0xED8A`| yhy |
|  `1`  |  | `0xED8C`| patonga |
|  `2`  |  | `0xED8C`| retonga |
|  `3`  |  | `0xED8C`| citonga |
|  `4`  |  | `0xED8C`| votonga |
|  `b`  |  | `0xED90`| by |
|  `d`  |  | `0xED91`| dy |
|  `g`  |  | `0xED92`| gy |
|  `v`  |  | `0xED93`| vy |
|  `r`  |  | `0xED94`| ry |
|  `z`  |  | `0xED95`| zy |
|  `j`  |  | `0xED96`| jy |
|  `n`  |  | `0xED97`| ny |
|  <code>`</code>  |  | `0xED98`| ba'abu |
|  `-`  |  | `0xED99`| smaji bu |
|  `,`  |  | `0xED9A`| slaka bu |
|  `~`  |  | `0xED9B`| tcena bu |
|  `a`  |  | `0xEDA0`| abu |
|  `e`  |  | `0xEDA1`| ebu |
|  `i`  |  | `0xEDA2`| ibu |
|  `o`  |  | `0xEDA3`| obu |
|  `u`  |  | `0xEDA4`| ubu |
|  `y`  |  | `0xEDA5`| ybu |
|  `A`  |  | `0xEDB0`| sepli me abu |
|  `E`  |  | `0xEDB1`| sepli me ebu |
|  `I`  |  | `0xEDB2`| sepli me ibu |
|  `O`  |  | `0xEDB3`| sepli me obu |
|  `U`  |  | `0xEDB4`| sepli me ubu |
|  `Y`  |  | `0xEDB5`| sepli me ybu |

All uppercase consonants should output their lowercase equivalent. All other characters should be passed through.