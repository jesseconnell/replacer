import sys
import argparse


def q(s): return "'{}'".format(s)

class Step(object):
    def __init__(self, old, new):
        self.__old = old
        self.__new = new

    def old(self, quoted=False):
        return q(self.__old) if quoted else self.__old

    def new(self, quoted=False):
        return q(self.__new) if quoted else self.__new

    def widths(self, quoted):
        return [len(self.old(quoted)), len(self.new(quoted))]

    def str(self, *widths):
        if not widths:
            widths = self.widths(True)
        fmt = "{{:{}}} => {{:{}}}".format(*widths)
        return fmt.format(self.old(True), self.new(True))


class Item(object):
    def __init__(self, old, new):
        tmp = "[{}:_temp_:{}_]".format(new[0], new[1:])
        self.__old = old
        self.__new = new
        self.__step1 = Step(old, tmp)
        self.__step2 = Step(tmp, new)

    def step1(self):
        return self.__step1

    def step2(self):
        return self.__step2

    def reversed(self):
        return Item(self.__new, self.__old)


class Plan(object):
    def __init__(self, items, symmetric):
        steps = []
        if type(items) is ItemList:
            items = items.items()

        for item in items:
            steps.append(item.step1())
        if symmetric:
            for item in items:
                steps.append(item.reversed().step1())
        for item in items:
            steps.append(item.step2())
        if symmetric:
            for item in items:
                steps.append(item.reversed().step2())
        self.__steps = steps
        self.__consistent = self.check_consistent()

    def check_consistent(self):
        consistent = True
        indices = range(int(len(self.steps())/2))
        for i1 in indices:
            s1 = self.steps()[i1]
            for i2 in indices:
                if i2 != i1:
                    s2 = self.steps()[i2]
                    if s1.new() in s2.old():
                        print("Conflict:  {:20} {}\nConflict:  {:20} {}".format("{} (new)".format(i1+1), s1.new(), "{} (old)".format(i2+1), s2.old()))
                        consistent = False
        return consistent

    def consistent(self):
        return self.__consistent
    def steps(self):
        return self.__steps

    def __widths(self):
        w1 = max(s.widths(True)[0] for s in self.steps())
        w2 = max(s.widths(True)[1] for s in self.steps())
        return [w1, w2]

    def __fmt(self):
        num_steps = len(self.steps())
        ws = len(str(num_steps)) + 1
        return "{{:{}}}  {{}}".format(ws)

    def show_plan(self):
        fmt = self.__fmt()
        step_no = 1
        widths = self.__widths()
        for step in self.steps():
            print(fmt.format(
                "{}.".format(step_no),
                step.str(*widths)))
            step_no += 1

    def do_replace_in_file(self, file_name, in_place=False):
        if not self.consistent():
            sys.stderr.write("strings are NOT consistent -- will not replace\n")
            return
        infile = open(file_name, 'r')
        out_file_name = file_name if in_place else "{}.ren".format(file_name)
        out_lines = []
        if infile:
            lines = [s for s in infile]
            for line in open(file_name, 'r'):
                for step in self.steps():
                    line = line.replace(step.old(), step.new())
                out_lines.append(line)
            infile.close()
            outfile = open(out_file_name, 'w')
            for line in out_lines:
                outfile.write(line)
            outfile.close()
            print("Wrote {}".format(out_file_name))


class ItemList(object):
    def __init__(self, pairs):
        self.__items = [Item(*pair) for pair in pairs]

    def items(self):
        return self.__items


def read_strings_file(input_file):
    l = []
    for s in input_file:
        a = s.strip()
        if not a:
            continue
        a = a.split(' ')
        if len(a) != 2:
            return None
        else:
            l.append(a)
    return l


def main():
    def error(s): sys.stderr.write("{}\n".format(s))
    parser = argparse.ArgumentParser(description='String Replacer/Swapper')
    parser.add_argument('input', type=str, help='file with strings to be replaced')
    parser.add_argument('file', metavar='file', type=str, nargs='*', help='file(s) to be processed')
    parser.add_argument('--swap', '-s', dest='swap', action='store_true')
    parser.add_argument('--inplace', '-i', dest='inplace', action='store_true')
    parser.add_argument('-t', '--test', dest='test', action='store_const',
                        const=sum, default=max,
                        help='sum the integers (default: find the max)')

    args = parser.parse_args()
    print(type(args))
    print("input: {}".format(args.input))
    print("file(s): {}".format(args.file))
    print("swap: ".format(args.swap))

    input_file = open(args.input)

    if not input_file:
        error("Could not open '{}'".format(args.input))
        sys.exit(1)
    pairs = read_strings_file(input_file)

    if not pairs:
            error("Input file '{}' not formatted properly.".format(args.infile))
            sys.exit(1)

    print(pairs)
    item_list = ItemList(pairs)
    plan = Plan(item_list, True)
    plan.show_plan()

    for f in args.file:
        plan.do_replace_in_file(f, args.inplace)


if __name__ == '__main__':
    main()
