# Circuit toolkit

Bench calculators in the browser, with the math done in Python.

- **Resistor color code**: click the bands, see the resistor and its value (4 or 5 bands)
- **Voltage divider**: output voltage, current and power in each resistor
- **RC filter**: cutoff frequency, time constant and a frequency-response plot (low-pass or high-pass)
- **LED resistor**: exact value, nearest standard E24 value, and the real current you'll get
- **Ohm's law**: give any two of voltage, current, resistance

Type values the way you'd say them on the bench: `4.7k`, `100n`, `20m`, `2.2M`.

## How it's put together

```
circuit-toolkit/
  circuit_toolkit/calc.py   the math: plain Python functions, no web code
  api/calculate.py          the web endpoint: takes JSON in, calls calc.py, sends JSON back
  public/index.html         the page you see: HTML, CSS and JavaScript in one file
  tests/test_calc.py        19 tests that check the math against known answers
  dev_server.py             runs the whole thing on your own computer
  vercel.json               tells Vercel to include calc.py with the endpoint
```

When you type in a box, the page sends your numbers to `/api/calculate`. That runs
`api/calculate.py`, which calls the matching function in `calc.py` and sends the answer
back. The page then draws it. Keeping the math in its own file means it can be tested
without a browser.

## Run it on your computer

You need Python 3 installed. From the project folder:

```
python3 dev_server.py
```

Then open http://localhost:3000. (On Windows, use `python` instead of `python3`.)

## Run the tests

```
python3 -m unittest discover tests
```

You should see `OK`. These check things like "1 kΩ and 1 µF gives a cutoff of 159.15 Hz".

## Put it on the internet with Vercel

Vercel is a hosting service. You give it your code, and it gives you a public link.
It runs `public/index.html` as the website and `api/calculate.py` as the Python endpoint.

1. **Put the project on GitHub.** Create a new empty repository on github.com named
   `circuit-toolkit`, then in the project folder run:
   ```
   git init
   git add .
   git commit -m "Circuit toolkit"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/circuit-toolkit.git
   git push -u origin main
   ```
2. **Sign in to vercel.com** with your GitHub account.
3. Click **Add New → Project**, find `circuit-toolkit`, and click **Import**.
4. Leave every setting as it is (Framework Preset: Other) and click **Deploy**.
5. After about a minute you get a link like `circuit-toolkit-yourname.vercel.app`.

From then on, every time you push a change to GitHub, Vercel rebuilds and updates the
site by itself. Put the link at the top of this README and on your resume.

If the page loads but every calculation fails, open the Vercel project, go to
**Logs**, and look at the error for `/api/calculate`. The most common cause is a
file path problem, and the error message will say which file it can't find.

## Ideas for making it yours

- Add a new tool, for example parallel and series resistors. Write the function in
  `calc.py`, add a test, add a branch in `api/calculate.py`, then add a form in
  `public/index.html`. That's the same pattern every existing tool follows.
- Add a second-order filter or a 555 timer calculator.
- Show the circuit diagram next to each result.
