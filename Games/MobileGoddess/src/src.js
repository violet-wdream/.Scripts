
(function (t) {
    var e = _0x38d07f,
      i = 2147483647;
    (t[e(197)] = function (t, e) {
      var n = _0x43df,
        s = t[n(207)]("/"),
        t = t[n(204)](s + 1),
        r = (s = (t =
          -1 < t[n(207)](n(217))
            ? t[n(192)](n(217), "")
            : -1 < t[n(207)](n(216))
            ? t[n(192)](n(216), "")
            : (t = (t = t[n(192)](n(206), ""))[n(192)](n(209), ""))[n(192)](
                n(193),
                ""
              ))[n(223)]("-"))[1]
          ? parseInt(s[1], 16)
          : i;
      for (r %= e[n(228)]; 3 * r < i; ) r *= 3;
      return r;
    }),
      (t[e(198)] = function (t, i) {
        for (
          var n = e,
            s = Math[n(205)](Math[n(200)](t[n(228)] / 4)),
            r = new Uint32Array(t, 0, s * s),
            a = s,
            o = s,
            h = 48;
          s < 2 * h;

        )
          h = Math[n(205)](s / 2);
        for (var l = 0; l < o; l++)
          for (var c = 0; c < a; c++) {
            var u = c,
              _ = l,
              d = !1;
            if (Math[n(205)](l / h) % 2 == 0) {
              if (
                (l + h < o ? (_ = l + h) : (d = !0),
                Math[n(205)](c / h) % 2 == 0)
              )
                c + h < a && (u = c + h);
              else {
                if (d) continue;
                u = c - h;
              }
              (d = l * a + c),
                (_ = _ * a + u),
                (u = r[d]),
                (r[d] = r[_] ^ i),
                (r[_] = u ^ i);
            }
          }
        return t;
      });
  })((gwcrypto = (window[_0x38d07f(201)] = gwcrypto) || {})),