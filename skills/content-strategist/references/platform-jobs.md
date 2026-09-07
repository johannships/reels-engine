# Platform jobs

Used by `content-strategist` at the format and channel step, and by
`brief-builder` when it shapes a brief for a named channel.

A channel is not a distribution pipe. It is a context that decides what the
reader already expected, how much attention they brought, what kind of proof
survives, and what a request is allowed to look like. The same thesis published
identically in six places fails in five of them, because five of those audiences
came for something else.

This file is opinionated on purpose. Disagree with a specific line rather than
ignoring the whole thing.

## At a glance

| Channel | Attention brought | Proof that survives | The one thing that kills it |
|---|---|---|---|
| YouTube | high, chosen deliberately | demonstration on screen | no visible thing happening |
| Short-form | near zero, interrupted | one legible visual moment | explaining before showing |
| LinkedIn | low, professional filter | a specific situation with numbers | posting a press release voice |
| X | low, argumentative | a claim plus a link or screenshot | needing three paragraphs of setup |
| Newsletter | high, granted by trust | reasoning worked through in full | selling before being useful |
| Blog | task-driven, arrived via search | reproducible steps and citations | answering a question nobody asked |

## YouTube

**What the viewer came for.** They chose this video over everything else on the
page, usually to see something done or to understand something they could not
get from text. They are willing to give real time, and they will leave the
moment it becomes clear no time was needed.

**Proof that works.** Demonstration. Screen recording, the actual build, the real
dashboard, the failure happening live. Video is the only channel where you can
show a process end to end and have people watch it, so spend the format on
things that must be seen. A talking head reading facts is a newsletter with worse
production economics.

**Typical failure mode.** Front-loading context. Twelve minutes of background
before the thing works. The viewer cannot tell whether the payoff exists, so they
leave during the setup. Show the result early, then earn the rest.

**How the CTA differs.** Video CTAs are cheap to place and easy to ignore, so
place one, spoken, at the point where the viewer has just got value, not at the
end where they have already left. Link it in the description because nobody types
URLs from video. One ask. Subscribe plus download plus comment is three asks and
gets none.

## Short-form

Vertical, sub-60-second, algorithmic feed. Treat Reels, Shorts and TikTok as one
job even though the audiences differ.

**What the viewer came for.** Nothing. They did not choose you. They were
scrolling and you interrupted. Every structural decision follows from that.

**Proof that works.** One visual moment that is legible without sound and without
context. A before and after. A number on screen. A thing visibly breaking. If the
proof needs a sentence of setup to make sense, it does not survive here.

**Typical failure mode.** Explaining before showing, which is how a person talks
when they have an audience already. Second failure mode: making short-form a
trailer for the long piece. A clip that only makes sense if you go watch
something else is a clip nobody finishes.

**How the CTA differs.** Usually `no CTA`, or at most one soft pointer. The
platform's own mechanics decide reach, and asking a stranger who has known you
for nine seconds to do anything converts badly. Let the piece be complete. The
honest next step is that they watch it again or follow.

## LinkedIn

**What the reader came for.** Professional self-interest. Something they can use
at work, or something that tells them how their field is changing. They are
skimming between meetings with a strong filter for corporate noise.

**Proof that works.** A specific situation, told plainly, with real numbers and a
real constraint. "We ran the migration twice, the second one took four hours
instead of three days, here is what changed" beats any framework diagram. First
person and concrete outperforms institutional and general, which is why company
pages underperform individuals saying the same thing.

**Typical failure mode.** Press release voice. Announcements about things the
reader has no stake in. The other failure is the engagement-bait shape: one-line
paragraphs, manufactured suspense, a lesson that turns out to be a platitude.
That format is recognisable now and it costs credibility with exactly the senior
readers worth reaching.

**How the CTA differs.** Small and lateral. A question worth answering, or a
pointer to a longer piece. Anything that reads like a sales motion in a feed post
gets penalised socially before it gets penalised algorithmically. Save the direct
ask for the newsletter, where you were invited.

## X

**What the reader came for.** The current argument. Speed, positions, and
reactions. They will read one screen. They will not read your setup.

**Proof that works.** A claim stated flatly, plus something checkable in the same
view: a screenshot, a chart, a quote with attribution, a link. The claim has to
be able to stand alone, because it will be quoted without your context and
sometimes without your qualifier.

**Typical failure mode.** Needing context. If the point requires three
paragraphs before it lands, it is not an X post, it is a newsletter section. The
second failure mode is stating a strong claim without the checkable artifact in
frame, which invites a pile-on you cannot answer with a source.

**How the CTA differs.** Almost always `no CTA` in the post itself. If there is a
link, expect the platform to suppress it and expect most readers not to click.
Write the post so it is worth reading even if nobody leaves. Threads should have
their payoff distributed rather than withheld until the last post.

## Newsletter

**What the reader came for.** They gave you their address, which means they
opted into a relationship and expect a return on it. Attention here is the
highest quality you will get and the easiest to spend permanently.

**Proof that works.** Reasoning shown in full. This is the one channel where you
can walk through how you reached a conclusion, include what you got wrong, and
show the working. Long is fine when the length is the reasoning. Long is not fine
when it is padding.

**Typical failure mode.** Selling before being useful. The second is
inconsistency of value, not of schedule: readers forgive a late issue and
unsubscribe from a thin one. The third is treating it as a broadcast of links you
posted elsewhere, which teaches people the email contains nothing new.

**How the CTA differs.** This is the channel where a direct ask is legitimate,
because the reader chose the relationship. One ask, at the end, sized to what the
issue delivered. If the issue was an argument rather than a solution, `no CTA`
still applies. A newsletter that asks every week without ever finishing something
useful trains people to scroll past the last section.

## Blog

Includes documentation-style posts and anything durable on a site you own.

**What the reader came for.** A task. They searched a specific problem, or an
assistant surfaced your page while answering someone's question. They arrived
mid-problem and will leave the second they see the answer is not here.

**Proof that works.** Reproducible steps, real commands, real configuration,
version numbers, and citations they can follow. This is the only channel with
durable value from precision, because the same page keeps answering the same
question for years. It is also the only channel where being wrong stays wrong in
public indefinitely, so date the time-sensitive parts and say which version you
tested.

**Typical failure mode.** Answering a question nobody asked, in the voice of an
article rather than an answer. The long preamble before the actual command is the
classic version. The other failure is publishing a thin new page next to a
stronger existing one, so the two compete for the same reader and neither wins.

**How the CTA differs.** Contextual and low friction. The reader is mid-task, so
the useful next step is usually another page that continues the task, or a
resource that makes the task easier. Interrupting a working solution with a
booking request wastes the credibility the page just built. Put the ask after the
problem is solved.

## Adapting one thesis without cross-posting

The correct relationship between channels is not "long version and short
versions". It is one thesis, different jobs.

Worked example. Thesis: teams keep rewriting their retrieval layer because they
are measuring the wrong thing.

- **Blog** the reference. The evaluation setup, the numbers, the citations, the
  code someone can run. This is what everything else points at.
- **YouTube** the demonstration. Run both evaluation setups on screen and let the
  viewer watch the wrong metric look fine while the system fails.
- **Newsletter** the reasoning. How this conclusion was reached, including the
  version that was wrong first.
- **LinkedIn** the situation. One team, one rewrite, what it cost, what they
  measure now.
- **X** the claim. The single counterintuitive line plus the chart from the blog
  post.
- **Short-form** the moment. The two numbers side by side, on screen, in nine
  seconds.

Every item is complete on its own. None of them requires another to make sense.
That is the test for whether the adaptation is real or whether it is one asset
reposted six times.

## Deliberate limits

- No claims about how any algorithm ranks content. Ranking behaviour changes
  without notice and is not published, so a strategy built on it is a strategy
  built on a guess. Everything above is about reader intent, which is stable.
- No posting frequency guidance. It depends on capacity, and thin frequent
  output loses to solid infrequent output on every channel here.
- No promised outcomes. A channel being a good fit for a thesis is a reason to
  expect the piece to be understood. It is not a reason to expect reach.
