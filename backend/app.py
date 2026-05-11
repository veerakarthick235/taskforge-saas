Experiment: Logical Operations in 8051 Microcontroller Using Simulator


---

FLOW CHART (Left Side)

┌───────────────┐
 │    START      │
 └──────┬────────┘
        │
        ▼
 ┌────────────────────┐
 │ Load data into     │
 │ accumulator and    │
 │ register           │
 └──────┬─────────────┘
        │
        ▼
 ┌────────────────────┐
 │ Perform logical    │
 │ operations         │
 │ AND / OR / XOR     │
 └──────┬─────────────┘
        │
        ▼
 ┌────────────────────┐
 │ Store result in    │
 │ memory/register    │
 └──────┬─────────────┘
        │
        ▼
 ┌────────────────────┐
 │ Display output in  │
 │ simulator          │
 └──────┬─────────────┘
        │
        ▼
 ┌───────────────┐
 │     STOP      │
 └───────────────┘


---

PROGRAM (Left Side)

ORG 0000H

MOV A,#55H      ; Load first data into accumulator
MOV R0,#0FH     ; Load second data into register

ANL A,R0        ; Perform AND operation

MOV R1,A        ; Store AND result

MOV A,#55H      ; Reload first data
ORL A,R0        ; Perform OR operation

MOV R2,A        ; Store OR result

MOV A,#55H      ; Reload first data
XRL A,R0        ; Perform XOR operation

MOV R3,A        ; Store XOR result

END


---

AIM (Right Side)

To perform logical operations such as AND, OR, and XOR using 8051 microcontroller in simulator.


---

REQUIRED ITEMS (Right Side)

PC or Laptop

8051 Simulator Software

Embedded C / Assembly IDE

8051 Microcontroller Kit (optional)



---

ALGORITHM (Right Side)

1. Start the program.


2. Load the first data into accumulator.


3. Load the second data into register.


4. Perform AND operation and store the result.


5. Perform OR operation and store the result.


6. Perform XOR operation and store the result.


7. Display the output in simulator.


8. Stop the program.




---

PROCEDURE (Right Side)

1. Open the 8051 simulator software.


2. Create a new assembly language program.


3. Type the given program and save it.


4. Compile the program without errors.


5. Execute the program in simulator.


6. Observe accumulator and register values.


7. Verify the results of logical operations.




---

CIRCUIT DIAGRAM

+-------------------+
        |     8051 MCU      |
        |                   |
        |    Simulator      |
        |                   |
        +-------------------+

(For simulator-based experiment, external hardware connection is not mandatory.)


---

RESULT

The logical operations AND, OR, and XOR were successfully performed using 8051 microcontroller simulator and the output was verified.


---

RESULT SCREENSHOT

(Insert simulator output screenshot here.)
