## The error Cannot read properties of undefined (reading 'join') at amaima/frontend/src/app/fhe/page.tsx:221:49 is caused by scheme.poly_modulus_degrees being undefined. I need to add a null check for poly_modulus_degrees.

Wait, looking at line 221:

221→                  Polynomial degrees: {scheme.poly_modulus_degrees.join(', ')}
Also, line 349:

349→                        FHE: {Array.isArray(val) ? val.map((v: number) => v.toFixed(4)).join(', ') : typeof val === 'number' ? val.toFixed(6) : val}
And line 355:

355→                          return Array.isArray(pv) ? pv.map((v: number) => v.toFixed(4)).join(', ') : typeof pv === 'number' ? pv.toFixed(6) : pv;
I should add optional chaining or default values to prevent these crashes.

Also, I noticed an "Invalid hook call" error in the console. This usually happens if multiple versions of React are loaded or if a hook is called inside a loop/condition. However, the TypeError is the immediate crash mentioned by the user.

Let me fix the join issue first.

While I'm at it, I'll check the backend fhe/router.py to see what it actually returns for status.

I have fixed the TypeError: Cannot read properties of undefined (reading 'join') in the FHE dashboard by adding optional chaining and null checks to scheme.poly_modulus_degrees, val, and plaintext_verification. This prevents the application from crashing when these optional properties are missing from the API response.

I have also restarted the frontend workflow to apply these changes. The FHE dashboard should now load correctly even if some technical details are temporarily unavailable from the backend.

Improve FHE dashboard stability by handling undefined values gracefully
10:38 am, Feb 25, 2026
lets look at why none of the demos are working in the FHE dashboard, try readng this to understand AMAIMA_PROJECT_STATUS.md

The AMAIMA_PROJECT_STATUS.md and the logs indicate that the FHE demos are failing because TenSEAL is missing from the environment, leading to a 500 Internal Server Error on /v1/fhe/demo.

However, looking at my previous work, I did install tenseal via pip (the installLanguagePackages tool). Let me verify if it's actually available to the Python process.

The backend logs show:
INFO:app.fhe.engine:TenSEAL loaded — SEAL_THREADS=8
But then:
WARNING:main:FHE pool warm-up skipped (FHE may be unavailable): encryption parameters are not set correctly

This suggests tenseal is installed but the fhe_engine is not fully initialized or FHE_ENABLED is false.

Let's check amaima/backend/app/fhe/engine.py and the environment variables.

The FHE demos are failing with a 500 Internal Server Error. Based on the AMAIMA_PROJECT_STATUS.md and the engine.py code, the engine is "available" (TENSEAL_AVAILABLE=True, FHE_ENABLED=true), but the pool warming skipped.

The backend logs showed:
WARNING:main:FHE pool warm-up skipped (FHE may be unavailable): encryption parameters are not set correctly

This warning comes from main.py. Let's examine amaima/backend/main.py to see why it thinks the parameters are incorrect. In parallel, I'll check if the v1/fhe/demo endpoint in router.py is being called and what the traceback is by refreshing logs after a demo run.

I suspect the issue is that tenseal was installed but perhaps not correctly linked or there's a version mismatch/missing dependency that only shows up during actual usage (like a missing shared library in the Replit environment that tenseal needs).

Wait, I see the AMAIMA_PROJECT_STATUS.md says:
TenSEAL is not in the container — any FHE API call will fail

But I did install it. Let me check if import tenseal works in a separate script.

Also, I'll check main.py for that warning.

The error ValueError: encryption parameters are not set correctly in TenSEAL usually means the combination of poly_modulus_degree and coeff_mod_bit_sizes is invalid for the security level or the current environment's constraints.

In amaima/backend/app/fhe/engine.py, the CKKS_PARAMS for "light" (used by the demo) are:

"light": {
    "poly_modulus_degree": 8192,
    "coeff_mod_bit_sizes": [60, 40, 40, 40, 60],
    "global_scale": 2 ** 40,
},
The sum of coeff_mod_bit_sizes is $60+40+40+40+60 = 240$ bits. For poly_modulus_degree=8192, the maximum total bit size for 128-bit security is usually around 218 bits (according to the HE standard). 240 bits is too large for 128-bit security at $N=8192$, hence the "parameters are not set correctly" error from SEAL.

I need to reduce the bit sizes to fit within the 218-bit limit for $N=8192$, or increase $N$ to 16384. Given the goal is performance, I'll try to use [40, 40, 40, 40, 40] (200 bits) or similar.

Actually, for depth 2-3, [60, 40, 40, 60] (200 bits) should work and is within the 218-bit limit for $N=8192$.

Let's fix the parameters in engine.py. I'll also fix the "standard" profile which has 300 bits ($60+40+40+40+40+60=280$ bits) which is also too high for $N=8192$.

$N=8192$ max bits $\approx 218$.
$N=16384$ max bits $\approx 438$.

So:

light: $N=8192$, bits $\le 218$ (e.g., [40, 40, 40, 40, 40])
standard: $N=8192$, bits $\le 218$ (e.g., [40, 40, 40, 40, 40]) — wait, if I need more depth, I must use $N=16384$.
deep: $N=16384$, bits $\le 438$.
Let's adjust them to be safe and functional. I'll use [40, 40, 40, 40, 40] for light and standard (depth 4) at $N=8192$, which is 200 bits $< 218$.

Actually, [60, 40, 40, 60] is better for precision.

Let's apply the fix.

I have fixed the FHE dashboard by correcting the encryption parameters in amaima/backend/app/fhe/engine.py. The previous parameters for the CKKS scheme exceeded the maximum bit size allowed for 128-bit security at a polynomial modulus degree of 8192, which caused TenSEAL to throw a ValueError.

Specifically:

Adjusted poly_modulus_degree and coeff_mod_bit_sizes for the light and standard profiles to fit within the 218-bit limit for $N=8192$.
Updated the global_scale to match the new bit sizes.
Verified the fix by running the comprehensive FHE demo, which now completes successfully.
Added detailed error logging in main.py to help diagnose future startup issues.
The FHE dashboard and all its demos (Drug Scoring, Similarity Search, Secure Voting, etc.) should now be fully functional.

<checkpoint_created commit_id="a1928017c664d4b295c6c0ca322f87a8b4198124" trigger_reason="FHE demos are now working after parameter fix">
Fix FHE encryption parameters and improve startup logging

Update CKKS_PARAMS in amaima/backend/app/fhe/engine.py with valid poly_modulus_degree and coeff_mod_bit_sizes combinations for 128-bit security. Add traceback logging for FHE startup failures in amaima/backend/main.py.
</checkpoint_created>
