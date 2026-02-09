#!/usr/bin/env python3
"""
指定テキストを1ページごとに配置したPDFを生成（50ページ）
"""
import argparse
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import mm

SAMPLE_TEXT = """思ったが、その通りだった。三回目の席で、わたしは彼の軍服から金の矢を外し、銀の記章に描きかえなければ
ならなかった。
「おめでとうございます、将
軍」
「ワシントンに転勤だ」と彼はため息をついた。 「でもまあ、町は民がいてこそ成り立つものだからな」
「それに、そこで生まれた民も
の意味するところは理解できなかったが、
」と、わたしは分かったようなふりをして言った。わたしは、彼の不明瞭な格言
それに対してどのように返答すべきかは分かっていた。
「さすがだ、チク・タク。さすがだね。知性という観点で、きみとわたしの波動はぴったりだ。人間にはあまり
いないタイプだ。ロボットにわたしの考
えが通じるというのもおかしな話だがね。人間よりずっと賢いロボットもいるんだってことだな。きみがワシン
トンに来られないなんて残念だ、アイデ
アを出しあうのはきみのためにもなるだろうに。実際......」と、彼はカードに走り書きした。
「実際、もしきみが所有者や芸術から離れてすこし休みたくなったら、ペンタゴンに連絡してくれ。きみを接収
するよ」
「そんなことできるんですか?」
「国家安全保障のためなら何でもできる。わたしは上層部のそのまた上層部で働いているんだ。この件で大統領
とは非常に密に連絡を取り合っている
し」
「ご冗
談でしょう?」
「大統領はマジにきみに注目してる。大マジだよ、チク・タク。そして、大統領が動くということは
コードは片腕で大仰な弧を描いてみせ、ものの見事にテディベアの歯に指の関節をぶつけた。わたしは彼を手洗
いにつれていき、冷水で出血を止めた。
そして、星条旗があしらわれた絆創膏を巻いた。
そのときまで、政治について考えたことはなかった。
新聞は航空事故の犠牲者家族の記事でいっぱいだった。わたしは家庭用の安いプリンターを手に入れ、こんな手
紙を何通か書いた。
スミス夫人へ
ご主人と二人のお子さんを飛行機事故で亡くされたのですね。残念なことです。保険金
も使い果たし、さぞかし
心細いことでしょう! 正直な話、
あなたとご主人の仲の良さは、ご近所中がご存知でしたよね。わたしが知りたいのは、誰が爆弾を仕掛けたの
か? ということです。あなた、それ
とも浮
気相手? ご主人が子供は自分の子じゃないと知って、あなたから逃れようとして?"""

def draw_wrapped_text(c, text, x, y, max_width, leading):
    # シンプルな行折り返し（禁則等は考慮しない）
    lines = []
    for raw_line in text.split("\n"):
        if not raw_line:
            lines.append("")
            continue
        line = ""
        for ch in raw_line:
            test = line + ch
            if pdfmetrics.stringWidth(test, "HeiseiMin-W3", 10) <= max_width:
                line = test
            else:
                lines.append(line)
                line = ch
        lines.append(line)
    
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def generate_pdf(output_path: Path, pages: int):
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # 日本語フォント
    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))
    c.setFont("HeiseiMin-W3", 10)

    margin_x = 20 * mm
    margin_y = 20 * mm
    max_width = width - 2 * margin_x
    leading = 14

    for _ in range(pages):
        y = height - margin_y
        draw_wrapped_text(c, SAMPLE_TEXT, margin_x, y, max_width, leading)
        c.showPage()

    c.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=50)
    parser.add_argument("--output", type=str, default="capture/sample_text_50pages.pdf")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    generate_pdf(output, args.pages)
    print(f"✅ PDF作成完了: {output}")
