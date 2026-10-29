from main import parse_args


def test_defaults():
    args = parse_args([])
    assert args.seed == "https://books.toscrape.com/"
    assert args.max_pages == 10
    assert args.max_depth == 1
    assert args.delay == 1.0
    assert args.allow_domain == []


def test_flags():
    args = parse_args(
        [
            "https://example.com/",
            "--max-pages",
            "5",
            "--max-depth",
            "0",
            "--delay",
            "2.5",
            "--allow-domain",
            "a.com",
            "--allow-domain",
            "b.com",
        ]
    )
    assert args.seed == "https://example.com/"
    assert args.max_pages == 5
    assert args.max_depth == 0
    assert args.delay == 2.5
    assert args.allow_domain == ["a.com", "b.com"]


def test_bad_values_are_rejected():
    # argparse calls sys.exit(2) on a bad value, which raises SystemExit
    bad_inputs = [
        ["--max-pages", "0"],
        ["--max-depth", "-1"],
        ["--delay", "-1"],
        ["example.com"],  # seed without http:// or https://
        ["--max-pages", "ten"],  # not a number
    ]
    for argv in bad_inputs:
        try:
            parse_args(argv)
        except SystemExit:
            continue
        raise AssertionError(f"expected an error for {argv}")


if __name__ == "__main__":
    test_defaults()
    test_flags()
    test_bad_values_are_rejected()
    print("All cli tests passed")
