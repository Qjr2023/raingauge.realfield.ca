// Partner and sponsor logos, served from public/logos/ (BASE_URL already ends with a slash).
// Shared by the footer carousel and the info modal so the two lists cannot drift apart.
const logo = (name) => `${import.meta.env.BASE_URL}logos/${name}.png`;

export const PARTNER_LOGOS = [
  { src: logo('agbio'), alt: 'College of Agriculture and Bioresources' },
  { src: logo('aci'), alt: 'Agronomic Crop Imaging Lab' },
  { src: logo('ndac'), alt: 'Nutrien Digital Agriculture Centre' },
  {
    src: logo('acreage'),
    alt: 'ACREAGE Digital Agriculture — Agroecosystem Digital Twins and Intelligent Systems',
  },
  { src: logo('realfield'), alt: 'RealField' },
];
