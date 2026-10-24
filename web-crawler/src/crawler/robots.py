from urllib.robotparser import RobotFileParser

def parse_robots(text):
    parser=RobotFileParser()
    parser.parse(text.splitlines())
    return parser
