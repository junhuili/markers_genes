#!/usr/bin/python
## ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** *****
##
## Example how to call this script using available examples:
## python 09.GenerateRandomConcatenationList.py -i ../examples/09.Subset_MarkersIds \
## --runs 1000 --previous ../examples/09.Already_generated_combinations
##
##
import sys, os, argparse
from string import strip
from hashlib import md5
from random import randint

## This code has been taken from a discussing on Stackoverflow
def list_powerset(lst):
  ## the power set of the empty set has one element, the empty set
  result = [[]]
  for x in lst:
    ## for every additional element in our set, the power set consists of the
    ## subsets that don't contain this element (just take the previous power
    ## set) plus the subsets that do contain the element (use list comprehension
    ## to add [x] onto everything in the previous power set)
    result.extend([subset + [x] for subset in result])
  return result

## Return all combinations for a given list of elements
def powerset(s):
  return frozenset(map(frozenset, list_powerset(list(s))))

## Return a valid id
def get_valid_id(already_found, start = 1):

  factor, length = 1000, 4
  while True:
    newId = str(start).zfill(length)
    if not newId in already_found:
      return newId
    start += 1
    if start > factor:
      factor, length = factor * 10, length + 1

def main(argv):

  parser = argparse.ArgumentParser()

  parser.add_argument("-i", "--in", dest = "inFile", required = True, type = \
    str, help = "Input file containing IDs of individual marker genes")

  strategy = parser.add_mutually_exclusive_group(required = True)

  strategy.add_argument("--exhaustive", dest = "exhaustive", default = False,
    action = "store_true", help = "Explore all possible combinations of marker "
    + "genes on the range [min_size - max_size]")

  strategy.add_argument("--runs", dest = "runSize", type = int, default = 0,
    help = "Generate 'run' number of different random combinations of marker "
    + "genes on the range [min_size - max_size]")

  parser.add_argument("--min_size", dest = "minSize", type = int, default = 2,
    help = "Set the minimum size of any combination generated by the program.")

  parser.add_argument("--max_size", dest = "maxSize", type = int, default = -1,
    help = "Set the maximum size of any combination generated by the program.")

  parser.add_argument("--previous", dest = "prevFile", type = str, default = "",
    help = "Input file containing already explored combinations")

  parser.add_argument("--delim", dest = "delim", type = str, default = "\t",
    help = "Delimiter e.g. <tab> of fields in the input file")

  parser.add_argument("--separator", dest = "separator", type = str, default = \
    ",", help = "Separator symbol e.g. ',' used to separate marker IDs")

  parser.add_argument("--column_comb", dest = "combColumn", default = 2, type =\
    int, help = "Column containing already generated combinations")

  parser.add_argument("--column_id", dest = "idColumn", type = int, default = 0,
    help = "Column containing the ID of each already generated combination")

  parser.add_argument("-o", "--out", dest = "outFile", type = str, default = "",
    help = "Output file")

  parser.add_argument("--verbose", dest = "verbose", default = False, action = \
    "store_true", help = "Active verbosity to see how entry are sorted")

  args = parser.parse_args()

  ## Check if the input files have been well defined.
  if not os.path.isfile(args.inFile):
    sys.exit(("ERROR: Check input IDs file '%s'")  % (args.inFile))

  ## Get IDs
  ids = map(strip, open(args.inFile, "rU").readlines())
  numbIds = len(ids)

  ## Check limits. minSize and maxSize are decrease/increase in 1 just to make
  ## greater than and lower than comparisons skipping the equal comparison.
  if args.maxSize > (numbIds - 1) or args.maxSize == -1:
    print >> sys.stderr, ("WARNING: Adjusting max_size to %d") % (numbIds - 1)
  maxSize = numbIds if args.maxSize > numbIds or args.maxSize == -1 else \
    args.maxSize + 1

  if args.minSize < 2:
    print >> sys.stderr, ("WARNING: Adjusting min_size to 2")
  if args.minSize >= maxSize:
    print >> sys.stderr, ("WARNING: Adjusting min_size to %d") % (maxSize - 1)

  minSize = 1 if args.minSize < 2 else maxSize - 2 if args.minSize >= maxSize \
    else args.minSize - 1

  previous, previous_ids = {}, set()
  ## Load previously explored combinations
  if args.prevFile and os.path.isfile(args.prevFile):
    for line in open(args.prevFile, "rU"):
      f = map(strip, line.split(args.delim))
      combination = map(strip, f[args.combColumn].split(args.separator))
      key = md5(",".join(sorted(combination))).hexdigest()
      if key in previous:
        print >> sys.stderr, ("WARNING: Same combination found more than one "
          + "time: '%s' - '%s'") % (line.strip(), previous[key][0])
        sys.stderr.flush()
      previous.setdefault(key, set()).add(line.strip())
      previous_ids.add(f[args.idColumn])

  ## Depending on the strategy selected, generate combinations exploring all of
  ## them in a given range of sizes or just get a subset of random combinations
  ## in a given range of sizes
  if args.exhaustive:
    all_combs = set([(len(e), ",".join(sorted(e))) for e in list_powerset(ids)
      if len(e) > minSize and len(e) < maxSize])

    valid = []
    for comb in sorted(all_combs):
      if md5(comb[1]).hexdigest() in previous:
        continue
      combId = get_valid_id(previous_ids)
      valid.append(("%s\t%d\t%s") % (combId, comb[0], comb[1]))
      previous_ids.add(combId)

    print >> sys.stderr, ("INFO: Found %d combinations after an exhaustive "
      "exploration. New ones: %d") % (len(all_combs), len(valid))

  ## Get 'n' random combinations -without repetitions- of input marker genes in
  ## a specific range size
  elif args.runSize > 0:

    ## Establish a condition for escaping from current loop after exploring an
    ## space of 100 times bigger of the combinations being asked
    found, escape = {}, args.runSize * 1000

    ## Adjust min/max size values as well as the number of ids. It's to reduce
    ## the sum/rest in the randint function
    minSize, maxSize, numbIds = minSize + 1, maxSize - 1, numbIds - 1

    while len(found) < args.runSize and escape > 0:
      escape -= 1
      ## Look for a randomly generated combination of size in [minSize, maxSize]
      ## Use a counter for getting out of combinations of a given size which
      ## have been all explored
      comb, comb_size, n = set(), randint(minSize, maxSize), 10000
      while len(comb) < comb_size and n > 0:
        comb.add(ids[randint(0, numbIds)])
        n -= 1

      comb_string = ",".join(sorted(comb))
      key = md5(comb_string).hexdigest()
      if len(comb) != comb_size or key in previous or key in found:
        continue

      found.setdefault(key, (comb_size, comb_string))

    ## Inform in case not all combinations have been generated
    if len(found) != args.runSize:
      sys.exit(("WARNING: Found '%d' combinations instead of '%d'. Adjust your "
        + "input parameters and/or execute again") % (len(found), args.runSize))

    valid = []
    for comb in sorted([found[d] for d in found]):
      combId = get_valid_id(previous_ids)
      valid.append(("%s\t%d\t%s") % (combId, comb[0], comb[1]))
      previous_ids.add(combId)

  oFile = open(args.outFile, "w") if args.outFile else sys.stdout
  print >> oFile, "\n".join(valid)
  oFile.close()
### ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ***** ****
if __name__ == "__main__":
  sys.exit(main(sys.argv[1:]))
