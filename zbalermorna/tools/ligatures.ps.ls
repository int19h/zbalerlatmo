log      = console.log.bind console
consonants = <[ ny dy ty zy sy gy jy xy iy ry my by py vy fy ky cy yhy uy ly denpabu denpabu.cas ]>
vowels = <[ abu ebu ibu obu ubu ybu aibu eibu oibu aubu ]>

for c in consonants
  log "/zbalermorna_" + c + " ["
  log " /" + c
  for v in vowels
    log " /" + v
    log " /" + c + "_" + v
  log "] def"
