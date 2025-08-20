# Reflections on this project and vibe coding in general

This file contains a collection of reflections on building this project mainly
using Claude Code. A majority of this code has been written while I was doing
something else, maybe not even in the same room.

## Code quantity

Claude tends to produce heaps and heaps of code. This code tends to work but it
has at least two drawbacks:

- It makes reviewing hard
- It makes further changes hard for the programmer but presumably also for
  itself. Both have a finite context window size.

## Code quality

Related to the above, while it can write nice code, sometimes it strays. In my
experience this has two causes:

- It doesn't quite understand what is asked but still tries. The resulting code
  might have nice properties but fails to do the correct thing.
- The code is just bad: convoluted, not idiomatic, etc.

Making frequent commits helps, frequent testing helps as well but both slow
down the pace of development significantly.

## Prototyping

For prototyping, Claude Code is unparalleled, starting from nothing to an
implementation of an idea may be done by writing 2 or 3 lazy prompts. You might
feel the need to throw it all away afterwards but you have something to play
with at least.

## Complex tasks

For complex tasks, such as extracting this functionality from the MealMCP
package, it isn't thorough enough. It does a bit of work and calls it a day but
it might not even be 10% done. It doesn't persist long enough once the task has
many steps although I thought that the steps were simple and small. For
example, getting rid of all references to meal and recipe related code was a
mostly manual task.

## Use git

Make frequent checkpoints and jump back to them when necessary. If the LLM gets
confused, stop the process, restore and restart.

## Nudge

If the circumstances are right, it will make big steps. When the circumstances
are not right, nudging along helps.
