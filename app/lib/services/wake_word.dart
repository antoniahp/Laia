/// Detecta «Oye Laia» aunque el reconocedor lo escriba raro: «oye Laya», «oiielais», «Olaya», «hola la ia»...
///
/// Compara cómo suena (sin tildes, y=i, ll=l, sin h, sin letras repetidas) y admite una letra de diferencia.
/// Para no saltar con «vamos a la playa», solo cuenta tras un saludo («oye», «hola»...) o al principio de la frase.
class WakeWord {
  static const _greetings = {'oie', 'oi', 'o', 'oe', 'ei', 'e', 'eh', 'ola', 'oia', 'oies', 'ai', 'elo', 'ok', 'okei'};
  static const _names = {'laia', 'lai', 'laiia', 'lalia', 'laila', 'laias', 'lais', 'laa', 'lia', 'lea', 'leia', 'leila', 'lila', 'leiia', 'liar', 'lair', 'laier', 'lier', 'liir'};

  static String _sound(String word) {
    var s = word.toLowerCase();
    const from = 'áàäâéèëêíìïîóòöôúùüûñç';
    const to = 'aaaaeeeeiiiioooouuuunc';
    for (var i = 0; i < from.length; i++) {
      s = s.replaceAll(from[i], to[i]);
    }
    s = s.replaceAll(RegExp(r'[^a-z]'), '').replaceAll('ll', 'l').replaceAll('y', 'i').replaceAll('h', '');
    return s.replaceAllMapped(RegExp(r'(.)\1+'), (m) => m.group(1)!); // «oiielais» → «oielais»
  }

  static int _distance(String a, String b) {
    final d = List.generate(a.length + 1, (i) => List.filled(b.length + 1, 0));
    for (var i = 0; i <= a.length; i++) {
      d[i][0] = i;
    }
    for (var j = 0; j <= b.length; j++) {
      d[0][j] = j;
    }
    for (var i = 1; i <= a.length; i++) {
      for (var j = 1; j <= b.length; j++) {
        final cost = a[i - 1] == b[j - 1] ? 0 : 1;
        d[i][j] = [d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost].reduce((x, y) => x < y ? x : y);
      }
    }
    return d[a.length][b.length];
  }

  // Cómo suele escribir el reconocedor en inglés «Hey Laia»: «Hailey», «Haley», «Hey Leah», «Hey Layer»...
  static const _joined = {
    'ailei', 'alei', 'eilei', 'eilia', 'ailaia', 'eilaia', 'elaia', 'alaia', 'elia', 'eilea', 'ailea',
    // «a liar», «hey liar», «love you», «hey lair»...
    'aliar', 'eiliar', 'liar', 'lair', 'eilair', 'alair', 'loveiou', 'eiloveiou', 'laier', 'eilaier', 'lier', 'eilier',
  };

  static bool _isName(String sound) =>
      _names.contains(sound) ||
      (sound.length >= 3 && _distance(sound, 'laia') <= 1) ||
      (sound.length >= 4 && sound.startsWith('l') && _distance(sound, 'laia') <= 2);

  /// ¿El sonido empieza por un saludo pegado al nombre? («oielaia», «olaia», «olalia»)
  static bool _greetingThenName(String sound) {
    for (final g in _greetings) {
      if (sound.length > g.length && sound.startsWith(g) && _isName(sound.substring(g.length))) return true;
    }
    return false;
  }

  /// Si la frase llama a Laia, devuelve lo que viene después (puede ser vacío). Si no, null.
  static String? after(String text) {
    final words = text.trim().split(RegExp(r'\s+')).where((w) => w.isNotEmpty).toList();
    final sounds = words.map(_sound).toList();
    for (var i = 0; i < words.length; i++) {
      final greeted = i > 0 && _greetings.contains(sounds[i - 1]);
      final atStart = i == 0 || (i == 1 && greeted);
      // una palabra («Laya»), dos juntas («la ia», «la ya») o saludo pegado («oiielais», «Olaya»)
      // de más larga a más corta, para no quedarse a medias («hola la ia» → «ola»+«la»+«ia»)
      final candidates = <(String, int)>[
        if (i + 2 < words.length) (sounds[i] + sounds[i + 1] + sounds[i + 2], 3),
        if (i + 1 < words.length) (sounds[i] + sounds[i + 1], 2),
        (sounds[i], 1),
      ];
      for (final (sound, used) in candidates) {
        final match = ((greeted || atStart) && _isName(sound)) ||
            (i == 0 && (_greetingThenName(sound) || _joined.contains(sound)));
        if (match) {
          return words.sublist(i + used).join(' ').replaceFirst(RegExp(r'^[,.;:!?¡¿\s]+'), '').trim();
        }
      }
    }
    return null;
  }

  /// La orden sin el «Oye Laia» del principio (si lo hay).
  static String clean(String text) {
    final rest = after(text);
    return (rest ?? text).trim();
  }
}
