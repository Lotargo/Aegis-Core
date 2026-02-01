# Moving Target Defense (MTD) Strategy

## Philosophy

The core idea of MTD is to increase the **uncertainty** and **complexity** for the attacker while maintaining **transparency** for the legitimate user.

In a static system, time works for the attacker. They can scan indefinitely.
In Aegis Core, time works against them. Information expires, paths change, and feedback is unreliable.

## 1. Information Hiding (The "Black Box")
Standard WAFs inspect traffic. Aegis Core **encapsulates** it.
By moving the routing information (`GET /admin/users`) into the encrypted layer, we deny the attacker the ability to map the application surface. They cannot distinguish a login attempt from a search query by looking at the wire.

## 2. Feedback Loop Disruption (Chaos Engineering)
Attackers rely on feedback loops:
*   "I sent a quote `'` and got a 500 error -> SQL Injection possible."
*   "I requested `/admin` and got 403 -> The folder exists."

Aegis Core disrupts this by injecting noise.
*   The attacker sends a malicious payload.
*   The system (Core B) blocks it or processes it safely.
*   The system returns a random status code (e.g., `404 Not Found`).
*   The attacker marks the payload as "ineffective" or the path as "non-existent".

This leads to **False Negatives** in vulnerability scanners, causing them to miss real entry points.

## 3. Ephemeral Access (Time-Based Security)
Static API keys are often leaked and used for months.
Aegis Core sessions are ephemeral.
*   A key is negotiated.
*   It is used for 10 minutes.
*   It is discarded.

Even if an attacker dumps the memory of a Core A instance, the keys they steal will be worthless in minutes. This forces the attacker to maintain a persistent presence to intercept new handshakes, increasing their risk of detection.
