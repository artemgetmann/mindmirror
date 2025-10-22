import { Navigation } from "@/components/Navigation";
import { HeroSection } from "@/components/HeroSection";
import { FeaturesSection } from "@/components/FeaturesSection";
import { WhyItMattersSection } from "@/components/WhyItMattersSection";
import { PrivacySection } from "@/components/PrivacySection";
import { PremiumWaitlistSection } from "@/components/PremiumWaitlistSection";
import { Footer } from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main>
        <HeroSection />
        <section id="how-it-works">
          <FeaturesSection />
        </section>
        <WhyItMattersSection />
        <PrivacySection />
        <PremiumWaitlistSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
