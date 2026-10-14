"""Testes da skill anime-motion-lab.   python3 -m unittest discover -s scripts/tests -v

As imagens/áudios de teste são SINAIS SINTÉTICOS desenhados aqui (formas geométricas, cliques de metrônomo) só para
ter gabarito conhecido — não são assets de edit. Testes de rede são pulados se o host estiver bloqueado.
"""
import http.server
import math
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import unittest
import wave

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from amllib import audio, effects, media, motion, plan, prep, project, qa, render, search, subject, util  # noqa


def write_wav(path, y, sr=22050):
    y = np.clip(y, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((y * 32767).astype(np.int16).tobytes())


def click_track(bpm=120, dur=12.0, sr=22050, booms=()):
    t = np.arange(int(dur * sr)) / sr
    y = np.zeros_like(t)
    period = 60.0 / bpm
    for b in np.arange(0, dur, period):
        i = int(b * sr)
        n = int(0.12 * sr)
        tt = np.arange(min(n, len(y) - i)) / sr
        y[i:i + len(tt)] += 0.6 * np.sin(2 * np.pi * (60 + 100 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 25)
    for b in booms:  # golpes graves fortes
        i = int(b * sr)
        n = int(0.6 * sr)
        tt = np.arange(min(n, len(y) - i)) / sr
        y[i:i + len(tt)] += 0.9 * np.sin(2 * np.pi * (110 * np.exp(-tt * 3) + 40) * tt) * np.exp(-tt * 5)
    return y * 0.8


def test_image(path, w=1600, h=900):
    """Cena sintética: fundo em degradê + 'personagem' (formas) no centro — gabarito para recorte/câmera."""
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=(30 + y * 120 // h, 60, 140 - y * 80 // h))
    for x in range(0, w, 80):
        d.line([(x, 0), (x + 200, h)], fill=(90, 110, 170), width=3)
    d.ellipse([w * .42, h * .15, w * .58, h * .45], fill=(240, 200, 160), outline=(0, 0, 0), width=6)
    d.rectangle([w * .38, h * .45, w * .62, h * .98], fill=(230, 120, 40), outline=(0, 0, 0), width=6)
    im.save(path)
    return path


class TestMotion(unittest.TestCase):
    def test_easing_endpoints(self):
        for name in motion.EASE:
            if name == "hold":
                continue
            self.assertAlmostEqual(motion.ease(name, 0), 0, places=3, msg=name)
            self.assertAlmostEqual(motion.ease(name, 1), 1, places=3, msg=name)

    def test_presets_and_interp(self):
        for p in motion.CAMERA_PRESETS:
            keys = motion.expand_preset(p, (0.3, 0.2))
            a, b = motion.interp_keys(keys, 0), motion.interp_keys(keys, 1)
            self.assertTrue(all(k in a for k in motion.FIELDS))
            self.assertGreaterEqual(min(a["z"], b["z"]), 1.0)

    def test_remap_monotonic(self):
        us = np.linspace(0, 1, 50)
        r = [motion.remap(u, [[0, 3], [0.4, 0.3], [1, 1]]) for u in us]
        self.assertAlmostEqual(r[0], 0, places=6)
        self.assertAlmostEqual(r[-1], 1, places=6)
        self.assertTrue(all(b >= a for a, b in zip(r, r[1:])))

    def test_impulse(self):
        self.assertEqual(motion.impulse(0.0, [(5.0, 1.0)]), 0.0)
        self.assertAlmostEqual(motion.impulse(5.0, [(5.0, 1.0)]), 1.0)
        self.assertLess(motion.impulse(5.5, [(5.0, 1.0)]), 0.1)


class TestAudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.wav = os.path.join(cls.tmp, "click.wav")
        cls.booms = [2.0, 6.25, 9.5]
        write_wav(cls.wav, click_track(120, 12, booms=cls.booms))
        cls.a = audio.analyze(cls.wav)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_tempo(self):
        self.assertAlmostEqual(self.a["tempo"], 120, delta=2.4)  # ±2%

    def test_beats_on_grid(self):
        b = np.array(self.a["beats"])
        err = np.abs(((b + 0.25) % 0.5) - 0.25)
        self.assertLess(float(np.median(err)), 0.035)  # ~1 quadro a 30 fps

    def test_impacts_found(self):
        imp = [i["t"] for i in self.a["impacts"] if i["strength"] > 0.5]
        for b in self.booms:
            self.assertTrue(any(abs(t - b) < 0.1 for t in imp), f"golpe em {b}s não detectado: {imp}")

    def test_structure(self):
        self.assertAlmostEqual(self.a["duration"], 12.0, delta=0.05)
        self.assertTrue(self.a["sections"])
        self.assertEqual(self.a["sections"][0]["start"], 0.0)


class TestSubject(unittest.TestCase):
    def test_resolve_known(self):
        g = subject.resolve("Goku")
        self.assertEqual(g["franquia"], "Dragon Ball")
        self.assertEqual(subject.resolve("Itachi")["franquia"], "Naruto")
        self.assertEqual(subject.resolve("Jesus")["preset"], "contemplativo")
        self.assertTrue(subject.resolve("Neymar").get("pessoa_real"))
        self.assertEqual(subject.resolve("Ronaldo", "o fenômeno de 2002")["nome"], "Ronaldo Nazário")
        self.assertTrue(subject.resolve("Personagem Desconhecido XYZ")["confirmar"])

    def test_manga_mode(self):
        g = subject.resolve("Goku", "edit só mangá")
        self.assertEqual(g.get("midia"), "manga")
        qs = subject.query_plan(g)
        self.assertGreater(len(qs), 10)
        self.assertTrue(all("manga" in q["query"].lower() for q in qs))
        self.assertNotIn("clipe", g["categorias"])

    def test_query_plan_categories(self):
        qs = subject.query_plan(subject.resolve("Goku"))
        cats = {q["categoria"] for q in qs}
        self.assertTrue({"close", "acao", "aberto", "clipe", "cena_famosa"} <= cats)
        self.assertGreater(len({q["query"] for q in qs}), 12)

    def test_relevance(self):
        g = subject.resolve("Goku")
        self.assertGreater(subject.relevance(g, "Goku Ultra Instinct official clip 4K"), 0.5)
        self.assertLess(subject.relevance(g, "Goku Black Rose AI generated art"), 0.2)
        self.assertLess(subject.relevance(g, "Naruto vs Sasuke final fight"), 0)

    def test_manga_check(self):
        self.assertEqual(subject.manga_check({"chroma_frac": 0.02, "hue_spread": 0.0}), "manga_pb")
        self.assertEqual(subject.manga_check({"chroma_frac": 0.7, "hue_spread": 0.05}), "manga_tingido")
        self.assertEqual(subject.manga_check({"chroma_frac": 0.7, "hue_spread": 0.6}), "colorido")


class TestMediaPrep(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_stats(self):
        p = test_image(os.path.join(self.tmp, "a.png"))
        d = media.describe_image(p)
        self.assertEqual((d["w"], d["h"]), (1600, 900))
        blur = Image.open(p).filter(__import__("PIL.ImageFilter", fromlist=["x"]).GaussianBlur(6))
        self.assertLess(media.sharpness(media._gray_small(blur)), d["sharpness"])
        g = Image.open(p).convert("L").convert("RGB")
        self.assertLess(media.image_stats(g)["chroma_frac"], 0.05)

    def test_fill_uses_only_existing_colors(self):
        im = Image.new("RGB", (400, 200), (220, 0, 0))
        ImageDraw.Draw(im).rectangle([200, 0, 400, 200], fill=(0, 0, 220))
        mask = Image.new("L", (400, 200), 0)
        ImageDraw.Draw(mask).ellipse([150, 50, 250, 150], fill=255)
        out = np.asarray(prep.fill_behind(im, mask), np.float32)
        hole = np.asarray(mask) > 128
        self.assertLess(out[hole][:, 1].max(), 12)  # nenhum verde 'inventado': só mistura de vermelho e azul

    def test_prep_without_segmentation(self):
        proj = os.path.join(self.tmp, "p")
        project.init_project(proj, "t", "270x480")
        aid = project.add_asset(proj, test_image(os.path.join(self.tmp, "b.png")))
        info = prep.prep_image(proj, aid, no_segment=True)
        self.assertEqual(info["technique"], "camera")
        self.assertEqual(len(info["focus"]), 2)


class TestEffects(unittest.TestCase):
    def test_shapes_and_ranges(self):
        f = np.random.default_rng(0).uniform(0, 255, (64, 36, 3)).astype(np.float32)
        for fn in [lambda x: effects.grade(x, "anime_rap"), lambda x: effects.glow(x, .5), lambda x: effects.chroma(x),
                   lambda x: effects.rgb_split(x, 4), lambda x: effects.glitch(x, 1, 3),
                   lambda x: effects.zoom_burst(x, .1), lambda x: effects.vignette(x, .4),
                   lambda x: effects.grain(x, .05, 2), lambda x: effects.light_sweep(x, .5),
                   lambda x: effects.invert(x), lambda x: effects.wave(x, 3)]:
            o = fn(f.copy())
            self.assertEqual(o.shape, f.shape)
            self.assertTrue(np.isfinite(o).all())

    def test_rgb_split_no_wrap(self):
        f = np.zeros((20, 20, 3), np.float32)
        f[:, :3, 0] = 255  # vermelho só na esquerda
        o = effects.rgb_split(f, 5)
        self.assertEqual(o[:, -5:, 0].max(), 0)  # nada 'dá a volta' para a direita


class TestSearchFetch(unittest.TestCase):
    def test_youtube_parser(self):
        data = {"contents": [{"videoRenderer": {"videoId": "abc123XYZ00", "title": {"runs": [{"text": "Goku clip"}]},
                                                "ownerText": {"runs": [{"text": "Canal"}]},
                                                "lengthText": {"simpleText": "1:00"}}}]}
        out = []
        search._walk_videos(data, out)
        self.assertEqual(out[0]["video_id"], "abc123XYZ00")
        self.assertEqual(out[0]["channel"], "Canal")

    def test_youtube_live(self):
        ok, why = search.host_reachable("www.youtube.com")
        if not ok:
            self.skipTest(f"YouTube inacessível aqui: {why}")
        res = search.search_youtube("Goku manga panel", limit=3)
        self.assertTrue(res)
        self.assertTrue(all(r["image_url"].startswith("https://i.ytimg.com/vi/") for r in res))

    def test_blocked_host_is_reported(self):
        ok, why = search.host_reachable("commons.wikimedia.org")
        if ok:
            self.skipTest("Commons acessível neste ambiente")
        self.assertIn("bloque", why.lower() + " bloque" if "proxy" in why.lower() else why.lower())

    def test_fetch_refuses_html(self):
        tmp = tempfile.mkdtemp()
        try:
            with open(os.path.join(tmp, "login.html"), "w") as f:
                f.write("<html>Sign in</html>")
            Image.new("RGB", (64, 64), (10, 20, 30)).save(os.path.join(tmp, "ok.png"))
            handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=tmp, **k)  # noqa
            with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
                port = httpd.server_address[1]
                th = threading.Thread(target=httpd.serve_forever, daemon=True)
                th.start()
                proj = os.path.join(tmp, "p")
                project.init_project(proj, "t")
                from amllib import fetch
                aid, e = fetch.download(proj, f"http://127.0.0.1:{port}/login.html")
                self.assertIsNone(aid)
                self.assertEqual(e["status"], "error")
                aid, e = fetch.download(proj, f"http://127.0.0.1:{port}/ok.png", license="CC0")
                self.assertTrue(aid)
                rec = project.load_manifest(proj)["assets"][aid]
                self.assertEqual(rec["source_url"], f"http://127.0.0.1:{port}/ok.png")
                self.assertEqual(rec["license_class"], "public_domain")
                httpd.shutdown()
        finally:
            shutil.rmtree(tmp)


class TestEndToEnd(unittest.TestCase):
    """Projeto completo em resolução pequena: imagem estática → parallax/câmera → render → QA."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.proj = os.path.join(cls.tmp, "proj")
        project.init_project(cls.proj, "e2e", "270x480")
        cls.aids = []
        for i in range(3):
            p = test_image(os.path.join(cls.tmp, f"img{i}.png"), 1200 + 100 * i, 800)
            aid = project.add_asset(cls.proj, p, role="teste")
            prep.prep_image(cls.proj, aid, no_segment=True)
            cls.aids.append(aid)
        # um 'clipe' existente (vídeo de teste do próprio ffmpeg)
        clip = os.path.join(cls.tmp, "clip.mp4")
        util.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=640x360:d=4:r=30",
                  "-pix_fmt", "yuv420p", clip])
        cls.clip = project.add_asset(cls.proj, clip, role="clipe")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_1_silent_edit(self):
        edit = plan.make_plan(self.proj, preset="rap", duration=4.0, assets=self.aids + [self.clip])
        self.assertAlmostEqual(sum(s["dur"] for s in edit["shots"]), 4.0, places=3)
        self.assertNotIn("audio", edit)
        out = render.render(self.proj, out=os.path.join(self.proj, "output", "mudo.mp4"), workers=2)
        rep = qa.validate(self.proj, out, sheet=False)
        self.assertTrue(rep["ok"], rep["errors"])
        info = util.video_info(out)
        self.assertEqual((info["w"], info["h"]), (270, 480))
        self.assertFalse(info["has_audio"])

    def test_2_music_sync(self):
        wav = os.path.join(self.tmp, "musica.wav")
        write_wav(wav, click_track(100, 5, booms=[2.4]))
        edit = plan.make_plan(self.proj, preset="rap", audio=wav, assets=self.aids)
        cuts = [s["start"] for s in edit["shots"][1:]]
        beats = audio.analyze(wav)["beats"]
        self.assertTrue(all(min(abs(c - b) for b in beats) < 0.02 for c in cuts), "corte fora da batida")
        out = render.render(self.proj, out=os.path.join(self.proj, "output", "sync.mp4"), workers=2)
        rep = qa.validate(self.proj, out, sheet=False)
        self.assertTrue(rep["ok"], rep["errors"])
        self.assertTrue(util.video_info(out)["has_audio"])

    def test_3_motion_is_continuous(self):
        """Câmera não trava na borda e dispara (regressão do teste do Goku)."""
        aid = self.aids[0]
        for preset, axis in (("pan_lr", "x"), ("tilt_down", "y")):
            edit = {"format": {"w": 270, "h": 480, "fps": 30}, "duration": 2.0, "grade": "neutro",
                    "shots": [{"asset": aid, "start": 0, "dur": 2.0, "technique": "camera",
                               "camera": {"preset": preset, "intensity": 0.8}}]}
            sr = render.ShotRenderer(self.proj, edit, render._prepare_shots(edit)[0], 270, 480, 30)
            vals = []
            for i in range(60):
                c = sr.camera(i / 30)
                S, cs, sn, ox, oy, pxc, pyc = sr._layer_map(c, 1.0)
                vals.append(pxc if axis == "x" else pyc)  # centro efetivo (depois do clamp), em px
            steps = np.abs(np.diff(vals))
            if preset == "pan_lr":
                self.assertGreater(steps[5:-5].min(), 0.01, "pan parou no meio")
            if steps.max() > 0:
                # sem 'trava e dispara': nenhum passo muito maior que a velocidade típica do movimento
                self.assertLess(steps.max(), 4 * np.median(steps[steps > 0]) + 1e-6, preset)
            sr.close()

    def test_4_sources_report(self):
        txt, warns = project.sources_report(self.proj)
        self.assertIn("| asset |", txt)
        self.assertTrue(os.path.exists(os.path.join(self.proj, "metadata", "FONTES.md")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
