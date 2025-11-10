import { Link } from "@heroui/link";
import { Snippet } from "@heroui/snippet";
import { Code } from "@heroui/code";
import { button as buttonStyles } from "@heroui/theme";
import { siteConfig } from "@/config/site";
import { title, subtitle } from "@/components/primitives";
import { GithubIcon } from "@/components/icons";
import { Card, CardHeader, CardBody, CardFooter } from "@heroui/card";
import { Image } from "@heroui/image";

export default function Home() {
  return (
    <div className="min-h-screen from-gray-50 to-gray-100">
      <section className="flex flex-col items-center justify-center gap-4 py-8 md:py-10">
        <div className="inline-block max-w-xl text-center justify-center">
          <span className={title()}>Возьми свой мозг&nbsp;</span>
          <span className={title()}>под контроль с&nbsp;</span>
          <span className={title({ color: "violet" })}>ИнгибитКонтроль&nbsp;</span>
          <br />
          <div className={subtitle({ class: "mt-4" })}>
            От Лаборатории «Аксон»
          </div>
        </div>
        <div className="flex gap-3">
          <Link
            isExternal
            className={buttonStyles({
              color: "primary",
              radius: "full",
              variant: "shadow",
            })}
            href={siteConfig.links.github}
          >
            Прокачать мозг
          </Link>
          <Link
            isExternal
            className={buttonStyles({ variant: "bordered", radius: "full" })}
            href={siteConfig.links.github}
          >
            <GithubIcon className="text-default-500" />
            GitHub
          </Link>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="text-3xl font-bold text-center mb-8">О тренажёре</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="p-4">
            <CardHeader className="flex gap-3">
              <Image
                alt="nextui logo"
                height={40}
                radius="sm"
                src="https://avatars.githubusercontent.com/u/86160567?s=200&v=4"
                width={40}
              />
              <div className="flex flex-col">
                <p className="text-lg">Ингибиторный контроль</p>
                <p className="text-small text-default-500">Улучшите свой самоконтроль</p>
              </div>
            </CardHeader>
            <CardBody>
              <p>Ингибиторный контроль — это способность управлять своими импульсами и эмоциями. Наш тренажёр поможет вам развить этот навык через series упражнений и задач.</p>
            </CardBody>
            <CardFooter>
              <Link isExternal showAnchorIcon href={siteConfig.links.github}>
                Узнать больше
              </Link>
            </CardFooter>
          </Card>

          <Card className="p-4">
            <CardHeader className="flex gap-3">
              <Image
                alt="nextui logo"
                height={40}
                radius="sm"
                src="https://avatars.githubusercontent.com/u/86160567?s=200&v=4"
                width={40}
              />
              <div className="flex flex-col">
                <p className="text-lg">Преимущества</p>
                <p className="text-small text-default-500">Что вы получите</p>
              </div>
            </CardHeader>
            <CardBody>
              <p>Развитие ингибиторного контроля поможет вам лучше концентрироваться, управлять своими эмоциями и принимать взвешенные решения.</p>
            </CardBody>
            <CardFooter>
              <Link isExternal showAnchorIcon href={siteConfig.links.github}>
                Узнать больше
              </Link>
            </CardFooter>
          </Card>

          <Card className="p-4">
            <CardHeader className="flex gap-3">
              <Image
                alt="nextui logo"
                height={40}
                radius="sm"
                src="https://avatars.githubusercontent.com/u/86160567?s=200&v=4"
                width={40}
              />
              <div className="flex flex-col">
                <p className="text-lg">Как начать</p>
                <p className="text-small text-default-500">Простые шаги</p>
              </div>
            </CardHeader>
            <CardBody>
              <p>Начните с регистрации и выполнения нескольких простых упражнений. Наш тренажёр адаптируется к вашему уровню и помогает вам прогрессировать.</p>
            </CardBody>
            <CardFooter>
              <Link isExternal showAnchorIcon href={siteConfig.links.github}>
                Начать сейчас
              </Link>
            </CardFooter>
          </Card>
        </div>
      </section>
    </div>
  );
}