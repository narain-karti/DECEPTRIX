import Navbar from "../components/shared/Navbar";
import Hero from "../components/shared/Hero";
import EvidenceCards from "../components/shared/EvidenceCards";
import UseCases from "../components/shared/UseCases";
import ImpactStats from "../components/shared/ImpactStats";
import Testimonials from "../components/shared/Testimonials";
import FinalCTA from "../components/shared/FinalCTA";
import Footer from "../components/shared/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <EvidenceCards />
        <UseCases />
        <ImpactStats />
        <Testimonials />
        <FinalCTA />
      </main>
      <Footer />
    </>
  );
}
