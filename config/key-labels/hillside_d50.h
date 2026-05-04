/*                              50 KEY MATRIX / LAYOUT MAPPING (Hillside Dactyl 50)
 *
 *  ╭─────────────────────────────────╮ ╭─────────────────────────────────╮
 *  │  0   1   2   3   4   5          │ │           6   7   8   9  10  11 │
 *  │ 12  13  14  15  16  17          │ │          18  19  20  21  22  23 │
 *  │ 24  25  26  27  28  29          │ │          30  31  32  33  34  35 │
 *  ╰────────╮ 36  37 ╭───────╮ 38 39 │ │ 40 41 ╭───────╮ 42 43 ╭─────────╯
 *           │        │ 44 45 │ 46    │ │    47 │ 48 49 │
 *           ╰────────╯       ╰───────╯ ╰───────╯       ╰────────╯
 *
 *  Logical labels (X_* slots are extras — bind via the matching macros in
 *  hillside_d50.keymap):
 *
 *      pos 0/11/12/23/24/35       outer pinky column → X_LT/X_LM/X_LB and
 *                                                      X_RT/X_RM/X_RB
 *      pos 36/37 (left)           raised pair        → X_LR (2 keys)
 *      pos 42/43 (right)          raised pair        → X_RR (2 keys)
 *      pos 38/39 (left)           thumb upper row    → X_LU (2 keys)
 *      pos 40/41 (right)          thumb upper row    → X_RU (2 keys)
 *      pos 44 (LH2) / 49 (RH2)    outer-bottom thumb → X_LH / X_RH
 *
 *  ╭─────────────────────────────────╮ ╭─────────────────────────────────╮
 *  │ X_LT LT4 LT3 LT2 LT1 LT0        │ │       RT0 RT1 RT2 RT3 RT4 X_RT  │
 *  │ X_LM LM4 LM3 LM2 LM1 LM0        │ │       RM0 RM1 RM2 RM3 RM4 X_RM  │
 *  │ X_LB LB4 LB3 LB2 LB1 LB0        │ │       RB0 RB1 RB2 RB3 RB4 X_RB  │
 *  ╰────────╯ X_LR ╭──────╮ X_LU     ╯ ╰   X_RU ╭──────╮ X_RR ╰──────────╯
 *                  │ X_LH LH1 LH0   │ │ RH0 RH1 X_RH │
 *                  ╰────────────────╯ ╰──────────────╯
 */

#pragma once

#define LT0  5  // left-top alpha row
#define LT1  4
#define LT2  3
#define LT3  2
#define LT4  1

#define RT0  6  // right-top alpha row
#define RT1  7
#define RT2  8
#define RT3  9
#define RT4 10

#define LM0 17  // left-middle alpha row
#define LM1 16
#define LM2 15
#define LM3 14
#define LM4 13

#define RM0 18  // right-middle alpha row
#define RM1 19
#define RM2 20
#define RM3 21
#define RM4 22

#define LB0 29  // left-bottom alpha row
#define LB1 28
#define LB2 27
#define LB3 26
#define LB4 25

#define RB0 30  // right-bottom alpha row
#define RB1 31
#define RB2 32
#define RB3 33
#define RB4 34

#define LH0 46  // inner-left thumb
#define LH1 45  // middle-left thumb
#define LH2 44  // outer-left thumb (X_LH slot)

#define RH0 47  // inner-right thumb
#define RH1 48  // middle-right thumb
#define RH2 49  // outer-right thumb (X_RH slot)
