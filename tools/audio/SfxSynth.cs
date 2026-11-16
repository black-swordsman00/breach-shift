// Original deterministic game effects. No recordings or third-party samples.
using System;
using System.IO;

public static class BreachShiftSfx
{
    const int Rate = 44100;
    const double Tau = Math.PI * 2;

    public static byte[] Render(string cue)
    {
        bool gun = cue == "pistol" || cue == "smg" || cue == "rifle" || cue == "shotgun";
        bool voice = cue.StartsWith("growl") || cue.StartsWith("hurt") || cue.StartsWith("death")
                     || cue == "attack" || cue == "howl" || cue == "roar";
        double duration = gun ? (cue == "smg" ? .29 : cue == "shotgun" ? .85 : .55)
                        : voice ? (cue.StartsWith("hurt") || cue == "attack" ? .48 : 1.65)
                        : cue == "reload_start" ? .66 : .30;
        int count = (int)(duration * Rate);
        double[] samples = new double[count];
        int seed = 17;
        foreach (char character in cue) seed = unchecked(seed * 31 + character);
        Random random = new Random(seed);
        double low = 0, phase = 0, peak = 0;
        double formant1 = 0, formant1Old = 0, formant2 = 0, formant2Old = 0;
        for (int i = 0; i < count; i++)
        {
            double t = (double)i / Rate;
            double noise = random.NextDouble() * 2 - 1;
            low += .13 * (noise - low);
            double value = 0;
            if (gun)
            {
                double basePitch = cue == "shotgun" ? 72 : cue == "smg" ? 185 : cue == "rifle" ? 130 : 155;
                phase += Tau * (basePitch * Math.Exp(-t * 14) + 38) / Rate;
                double blast = (noise - low) * Math.Exp(-t * (cue == "shotgun" ? 37 : 65));
                double body = Math.Sin(phase) * Math.Exp(-t * (cue == "shotgun" ? 11 : 24));
                double air = low * Math.Exp(-t * 15) * 2.4;
                value = Math.Tanh((blast * 1.7 + body * .9 + air) * 1.9);
                if (i > (int)(.028 * Rate)) value += samples[i - (int)(.028 * Rate)] * .18;
                if (i > (int)(.071 * Rate)) value += samples[i - (int)(.071 * Rate)] * .10;
            }
            else if (voice)
            {
                double fundamental = cue == "roar" ? 35 : cue == "howl" ? 92 : cue.EndsWith("2") ? 66 : 52;
                fundamental += 6 * Math.Sin(Tau * 2.8 * t);
                if (cue.StartsWith("death")) fundamental *= 1.0 - .5 * t / duration;
                if (cue == "howl") fundamental += 75 * Math.Sin(Math.PI * t / duration);
                phase += Tau * fundamental / Rate;
                double source = Math.Tanh(3.6 * Math.Sin(phase)) * .55 + noise * .16;
                double r = .985;
                double next1 = (1-r) * source + 2*r*Math.Cos(Tau*370/Rate)*formant1 - r*r*formant1Old;
                double next2 = (1-r) * source + 2*r*Math.Cos(Tau*980/Rate)*formant2 - r*r*formant2Old;
                formant1Old = formant1; formant1 = next1;
                formant2Old = formant2; formant2 = next2;
                double envelope = Math.Min(1, t/.055) * Math.Min(1, (duration-t)/.22);
                value = Math.Tanh((source*.35 + next1*2.1 + next2*1.1) * 1.6)
                        * envelope * (.8 + .2*Math.Sin(Tau*4.1*t));
            }
            else
            {
                double[] events = cue == "reload_start" ? new double[]{.01,.20,.43,.52}
                                  : cue == "reload_finish" ? new double[]{.01,.09}
                                  : new double[]{.005};
                foreach (double onset in events)
                {
                    double d = t - onset;
                    if (d >= 0)
                        value += noise*.65*Math.Exp(-d*100)
                               + Math.Sin(Tau*(cue == "ammo_pickup" ? 1250 : 620)*d)*.28*Math.Exp(-d*55)
                               + Math.Sin(Tau*155*d)*.45*Math.Exp(-d*45);
                }
            }
            value *= Math.Min(1, (duration-t)/.012);
            samples[i] = value;
            peak = Math.Max(peak, Math.Abs(value));
        }
        using (MemoryStream stream = new MemoryStream())
        using (BinaryWriter writer = new BinaryWriter(stream))
        {
            writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); writer.Write(36 + count*2);
            writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt ")); writer.Write(16);
            writer.Write((short)1); writer.Write((short)1); writer.Write(Rate); writer.Write(Rate*2);
            writer.Write((short)2); writer.Write((short)16);
            writer.Write(System.Text.Encoding.ASCII.GetBytes("data")); writer.Write(count*2);
            foreach (double sample in samples)
                writer.Write((short)(sample / Math.Max(peak, .001) * 28000));
            writer.Flush();
            return stream.ToArray();
        }
    }
}
