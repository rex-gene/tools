import pkm2png
import sys

if __name__ == '__main__':
    pkmName = sys.argv[1]
    outputName = sys.argv[2]

    pkmData = open(pkmName, 'rb').read()
    pngData = pkm2png.pkm2png(gen=10, data=pkmData)
    with open(outputName, 'w') as f:
        f.write(pngData)
