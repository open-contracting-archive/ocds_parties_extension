Conversion tool
===============

convert.py will update organisation references in 1.0 format to 1.1.

Current usage:

```
cat ../tests/test.json | python convert.py -c | less
```

which will output a list of releases to screen, converted in compatibility mode.

Remove ```-c``` or set ```-compat=False``` to remove backwards compatability.

### ToDo

* [ ] Write a downgrade tool